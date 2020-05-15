#!/usr/bin/python3

from __future__ import print_function

import logging
import argparse
import os
import socket
import subprocess
import sys
import traceback
import time
import shutil
import re

import htcondor
import classad

logger = logging.getLogger("register")
logger.setLevel(logging.ERROR + 10)

DEFAULT_PORT = "9618"
DEFAULT_TARGET = "htpheno-cm.chtc.wisc.edu:{}".format(DEFAULT_PORT)
REGISTRATION_CODE_PATH = "registration/code"
RECONFIG_COMMAND = ["condor_reconfig"]
TOKEN_BOUNDING_SET = ["READ", "ADVERTISE_STARTD"]
SOURCE_PREFIX = "SOURCE_"
SOURCE_POSTFIX = "htpheno-cm.chtc.wisc.edu"
NUM_RETRIES = 10
TOKEN_OWNER_USER = TOKEN_OWNER_GROUP = "condor"
SOURCE_CHECK = re.compile(r"^[a-zA-Z]\w*$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Register a source with the HT Phenotyping project."
    )

    parser.add_argument("--source", help="The source name to register.", required=True)

    parser.add_argument(
        "--pool",
        help="The pool to register with. Defaults to {}. If you specify a custom pool but don't include a port, the default port will be used ({}).".format(
            DEFAULT_TARGET, DEFAULT_PORT
        ),
        default=DEFAULT_TARGET,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose output. Useful for debugging.",
    )

    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    if args.verbose:
        # HTCondor library logging setup
        htcondor.param["TOOL_DEBUG"] = "D_FULLDEBUG D_SECURITY"
        htcondor.enable_debug()

        # Python logging setup
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s ~ %(message)s"
            )
        )

        logger.addHandler(handler)

    if not SOURCE_CHECK.match(args.source):
        error(
            "The source name must be composed of only alphabetical characters (A-Z, a-z), digits (0-9), and underscores (_). It may not begin with a digit."
        )

    if not is_admin():
        error(
            "This command must be run as root (on Linux/Mac) or as an administrator (on Windows)"
        )

    logger.debug('Setting SEC_CLIENT_AUTHENTICATION_METHODS to "SSL"')
    htcondor.param["SEC_CLIENT_AUTHENTICATION_METHODS"] = "SSL"

    # TODO: temporary fix for https://github.com/HTPhenotyping/registration/issues/17
    if htcondor.param["AUTH_SSL_CLIENT_CAFILE"] == "/etc/ssl/certs/ca-bundle.crt":
        htcondor.param["AUTH_SSL_CLIENT_CAFILE"] = "/etc/ssl/certs/ca-certificates.crt"

    success = request_token(pool=args.pool, source=args.source)

    if not success:
        error("Failed to complete the token request workflow.")

    print(
        'Sending a "reconfigure" command to HTCondor (so that it picks up the new token).'
    )
    reconfig()


def is_admin():
    try:  # unix
        return os.geteuid() == 0
    except AttributeError:  # windows
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() == 0


def request_token(pool, source):
    if ":" in pool:
        alias, port = pool.split(":")
    else:
        alias = pool
        port = DEFAULT_PORT
    ip, port = socket.getaddrinfo(alias, int(port), socket.AF_INET)[0][4]
    coll_ad = classad.ClassAd(
        {
            "MyAddress": "<{}:{}?alias={}>".format(ip, port, alias),
            "MyType": "Collector",
        }
    )
    logger.debug("Constructed collector ad: {}".format(repr(coll_ad)))

    htcondor.param["SEC_TOKEN_DIRECTORY"] = "/etc/condor/tokens.d"

    token = request_token_and_wait_for_approval(source, alias, collector_ad=coll_ad)

    if token is None:
        return False

    print("Token request approved!")

    token_dir = htcondor.param["SEC_TOKEN_DIRECTORY"]
    token_name = "50-{}-registration".format(alias)
    token_path = os.path.join(token_dir, token_name)

    logger.debug("Writing token to disk (in {})".format(token_dir))
    token.write(token_name)
    logger.debug("Wrote token to disk (at {})".format(token_path))

    logger.debug("Correcting token file permissions...")
    shutil.chown(token_path, user=TOKEN_OWNER_USER, group=TOKEN_OWNER_GROUP)
    logger.debug("Corrected token file permissions...")

    print("Registration of source {} with {} is complete!".format(source, alias))

    return True


def request_token_and_wait_for_approval(
    source, alias, collector_ad, retries=10, retry_delay=5
):
    """
    This function requests a token and waits for the request to be authorized.
    If the authorization flow is successful, it will return the token.
    Otherwise, it will return ``None``.

    Parameters
    ----------
    source
        The data source name to request a token for.
    alias
        The alias of the server (only used for user-facing messages).
    collector_ad
        The ClassAd used to contact the collector to make the token request to.
    retries
        The number of times to attempt the token authorization flow.

    Returns
    -------

    """
    start_time = None
    for attempt in range(1, retries + 1):
        if start_time is not None:
            elapsed_time = time.time() - start_time
            wait_time = retry_delay - elapsed_time
            if wait_time > 0:
                print(
                    "Waiting for ~{:.1f} seconds before retrying...".format(wait_time)
                )
                time.sleep(wait_time)

        start_time = time.time()

        print("Attempting to get token (attempt {}/{}) ...".format(attempt, retries))
        try:
            req = make_token_request(collector_ad, source)
        except Exception as e:
            logger.exception("Token request failed")
            print("Token request failed due to: {}".format(e))
            continue

        try:
            # TODO: the url construction here is very manual; use urllib instead
            print(
                "Token request is queued; please approve it by following the instructions at https://{}/{}?code={}".format(
                    alias, REGISTRATION_CODE_PATH, req.request_id
                )
            )
            print(
                "Token request ID is {} (if you need to enter it manually)".format(
                    req.request_id
                )
            )
            return req.result(0)
        except Exception as e:
            logger.exception("Error while waiting for token approval.")
            print("An error occurred while waiting for token approval: {}".format(e))


def make_token_request(collector_ad, source):
    identity = "{}{}@{}".format(SOURCE_PREFIX, source, SOURCE_POSTFIX)

    req = htcondor.TokenRequest(identity, bounding_set=TOKEN_BOUNDING_SET)
    req.submit(collector_ad)

    # TODO: temporary fix for https://github.com/HTPhenotyping/registration/issues/10
    # Yes, we could, in principle, hit the recursion limit here, but we would have to
    # get exceedingly unlucky, and this is a simple, straightforward fix.
    # Once we upgrade the server to whatever version of HTCondor this is fixed in,
    # we can drop this code entirely.
    if req.request_id.startswith("0"):
        logger.debug("Got a token with a leading 0; trying again.")
        return make_token_request(collector_ad, source)

    return req


def reconfig():
    subprocess.call(RECONFIG_COMMAND)


def error(msg, exit_code=1):
    print(
        "Error: {}\nConsider re-running with --verbose to see debugging information.".format(
            msg
        ),
        file=sys.stderr,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        error("Aborted!")
    except Exception as e:
        traceback.print_exc()
        error("Encountered unhandled error: {}".format(e))
