import collections
import subprocess
import os
import json

try:  # py3
    from configparser import ConfigParser
except ImportError:  # py2
    from ConfigParser import ConfigParser


from flask import Blueprint, request, current_app, make_response, render_template

code_bp = Blueprint(
    "code",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/code",
)


class CondorToolException(Exception):
    pass


@code_bp.route("/code", methods=["GET"])
def code_get():
    response = make_response(render_template("code_submit.html"))
    return response


SOURCE_PREFIX = "SOURCE_"
SOURCE_POSTFIX = "users.htcondor.org"


@code_bp.route("/code", methods=["POST"])
def code_post():
    request_id = request.form.get("code", None)

    if request_id is None:
        return error("The code parameter is missing", 400)
    if not request_id.isdigit():
        return error(
            'The request ID you entered was not a sequence of numbers (it was "{}"). Make sure it was copied correctly.'.format(
                request_id
            ),
            400,
        )

    try:
        user_id_env_var = current_app.config["USER_ID_ENV_VAR"]
    except KeyError:
        current_app.logger.error(
            "Config variable USER_ID_ENV_VAR not set; this should be set to the name of the environment variable that holds the user's identity (perhaps REMOTE_USER ?)"
        )
        return error("Server configuration error", 500)

    current_app.logger.debug(
        "Will read user ID from request environment variable {}".format(user_id_env_var)
    )

    user_id = request.environ.get(user_id_env_var, None)
    current_app.logger.debug("User ID is {}".format(user_id))
    if not user_id:
        return error("Unknown user", 401)

    try:
        result = get_pending_token_request(request_id)
    except CondorToolException as cte:
        current_app.logger.exception("Wasn't able to fetch token requests.")
        return error(str(cte), 400)

    if not result:
        return error("Request {} is unknown".format(request_id), 400)
    result = result[0]

    authz = result.get("LimitAuthorization")
    if authz != "ADVERTISE_STARTD":
        return error("Token must be limited to the ADVERTISE_STARTD authorization", 400)

    try:
        allowed_sources = get_allowed_sources(user_id)
    except Exception:
        current_app.logger.exception("Failed to get allowed sources.")
        return error("Server configuration error", 500)

    current_app.logger.debug(
        "Allowed sources for user {} are {}".format(user_id, allowed_sources)
    )

    if not allowed_sources:
        return error("User not associated with any known token identity", 400)

    found_requested_identity = False
    for source in allowed_sources:
        identity = "{}{}@{}".format(SOURCE_PREFIX, source, SOURCE_POSTFIX)
        if identity == result.get("RequestedIdentity"):
            found_requested_identity = True
            break

    if not found_requested_identity:
        return error(
            "Requested identity ({}) not in the list of allowed sources ({})".format(
                result.get("RequestedIdentity"), ", ".join(allowed_sources)
            ),
            400,
        )

    try:
        approve_token_request(request_id)
    except CondorToolException:
        current_app.logger.exception(
            "Token must be limited to the ADVERTISE_STARTD authorization."
        )
        return error("Token must be limited to the ADVERTISE_STARTD authorization", 400)

    context = {"info": "Request approved."}
    response = make_response(render_template("code_submit_success.html", **context))
    return response


def error(info, status_code):
    context = {"info": info}
    return make_response(
        render_template("code_submit_failure.html", **context), status_code
    )


def get_allowed_sources(user_id):
    """
    Map a given user ID to a list of sources they are authorized to register.
    """
    names_to_sources = {
        entry["name"]: entry["sources"].split() for entry in parse_humans_file()
    }
    return names_to_sources.get(user_id, [])


def parse_humans_file():
    try:
        humans_file = current_app.config["HUMANS_FILE"]
    except KeyError:
        current_app.logger.error(
            "Config variable HUMANS_FILE not set; this should be set to the path of the file containing the information on humans."
        )
        raise

    config = ConfigParser()
    config.read(humans_file)

    entries = config_to_entries(config)

    return entries


def config_to_entries(config):
    entries = []
    for section in config.sections():
        entry = {}
        for option in config.options(section):
            entry[option] = config.get(section, option)

        entries.append(entry)

    return entries


def get_pending_token_request(request_id):
    binary = current_app.config.get(
        "CONDOR_TOKEN_REQUEST_LIST", "condor_token_request_list"
    )
    args = [binary, "-reqid", str(request_id), "-json"]

    current_app.logger.debug("Running {}".format(" ".join(args)))

    process = subprocess.Popen(
        args,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env=make_request_environment(),
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise CondorToolException(
            "Failed to list internal requests: {}\nMake sure you entered the correct request ID.".format(
                stderr.decode("utf-8")
            )
        )
    try:
        json_obj = json.loads(stdout)
    except json.JSONDecodeError:
        raise CondorToolException("Internal error: invalid format of request list")
    current_app.logger.debug("Resulting token list:\n{}".format(json_obj))

    return json_obj


def approve_token_request(request_id):
    binary = current_app.config.get(
        "CONDOR_TOKEN_REQUEST_APPROVE", "condor_token_request_approve"
    )
    args = [binary, "-reqid", str(request_id)]

    current_app.logger.debug("Running {}".format(" ".join(args)))

    process = subprocess.Popen(
        args,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=make_request_environment(),
    )
    stdout, stderr = process.communicate(input=b"yes\n")

    if process.returncode:
        raise CondorToolException(
            "Failed to approve request: {}".format(stderr.decode("utf-8"))
        )


def make_request_environment():
    req_environ = dict(os.environ)
    req_environ.setdefault("CONDOR_CONFIG", "/etc/condor/condor_config")
    req_environ["_condor_SEC_CLIENT_AUTHENTICATION_METHODS"] = "TOKEN"
    req_environ["_condor_SEC_TOKEN_DIRECTORY"] = "/etc/condor/tokens.d"

    return req_environ
