#!/usr/bin/python3

from __future__ import print_function

import logging
import argparse
import os
import socket
import subprocess
import sys

import htcondor
import classad

logger = logging.getLogger("register")
logger.setLevel(logging.ERROR + 10)

DEFAULT_PORT = "9618"
DEFAULT_TARGET = "htpheno-cm.chtc.wisc.edu:{}".format(DEFAULT_PORT)
REGISTRATION_CODE_PATH = "registration/code"
RECONFIG_COMMAND = ["condor_reconfig"]
TOKEN_BOUNDING_SET = ["ADVERTISE_STARTD"]
SOURCE_POSTFIX = "users.htcondor.org"
NUM_RETRIES = 10


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

    if not is_admin():
        error(
            "This command must be run as root (on Linux/Mac) or as an administrator (on Windows)"
        )

    logger.debug('Setting SEC_CLIENT_AUTHENTICATION_METHODS to "SSL"')
    htcondor.param["SEC_CLIENT_AUTHENTICATION_METHODS"] = "SSL"

    pool = args.pool
    if not pool.startswith("<") and ":" not in pool:
        pool = "{}:{}".format(pool, DEFAULT_PORT)

    success = request_token(pool=args.pool, source=args.source)

    if success:
        print(
            "Sending a reconfigure command to HTCondor (so that it picks up the new token)."
        )
        reconfig()


def is_admin():
    try:  # unix
        return os.geteuid() == 0
    except AttributeError:  # windows
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() == 0


def request_token(pool, source):
    alias, port = pool.split(":")
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
        # TODO: provide support email here, once we have one
        print("Token request was not approved. Please try again.")
        return False

    print("Token request approved!")

    token.write("50-{}-registration".format(alias))
    print("Registration of source {} with {} is complete!".format(source, alias))

    return True


def request_token_and_wait_for_approval(source, alias, collector_ad):
    identity = "{}@{}".format(source, SOURCE_POSTFIX)

    for attempt in range(1, NUM_RETRIES + 1):
        print(
            "Attempting to get token (attempt {}/{}) ...".format(attempt, NUM_RETRIES)
        )
        try:
            req = htcondor.TokenRequest(identity, bounding_set=TOKEN_BOUNDING_SET)
            req.submit(collector_ad)
            reqid = req.request_id
        except Exception as e:
            logger.exception("Token request failed.")
            print("Token request failed.")
            continue

        try:
            # TODO: the url construction here is very manual; use urllib instead
            print(
                "Request is queued; please approve it by visiting https://{}/{}?code={}".format(
                    alias, REGISTRATION_CODE_PATH, reqid
                )
            )
            print("Request ID is {}".format(reqid))
            return req.result(600)
        except Exception as e:
            logger.exception("Exception while waiting for token approval.")
            print("An error occurred while waiting for token approval: {}".format(e))


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
        print("Aborted!", file=sys.stderr)
