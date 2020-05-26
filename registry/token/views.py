import subprocess
import os
import json
import re

from flask import Blueprint, request, current_app, make_response, render_template

from ..sources import get_user_id, get_sources
from ..exceptions import CondorToolException, ConfigurationError

token_bp = Blueprint(
    "token",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/token",
)


@token_bp.route("/token", methods=["GET"])
def code_get():
    response = make_response(render_template("code_submit.html"))
    return response


SOURCE_PREFIX = "SOURCE_"
SOURCE_POSTFIX = "htpheno-cm.chtc.wisc.edu"
SOURCE_CHECK = re.compile(r"^[a-zA-Z]\w*$")
ALLOWED_AUTHORIZATIONS = {"READ", "ADVERTISE_STARTD"}


@token_bp.route("/token", methods=["POST"])
def code_post():
    request_id = request.form.get("request_id", None)

    if request_id is None:
        return error("The request_id parameter is missing", 400)
    if not request_id.isdigit():
        return error(
            'The request ID you entered was not a sequence of numbers (it was "{}"). Make sure it was copied correctly.'.format(
                request_id
            ),
            400,
        )

    try:
        user_id = get_user_id()
    except ConfigurationError:
        return error(
            "Server configuration error. Please contact the administrators.", 500
        )

    if not user_id:
        return error("Unknown user", 401)

    try:
        result = get_pending_token_request(request_id)
    except CondorToolException:
        current_app.logger.exception("Error while fetching token requests.")
        return error(
            "Was not able to fetch token requests. Please try again or contact the administrators.",
            400,
        )

    if not result:
        return error("Request {} is unknown".format(request_id), 400)
    result = result[0]

    requested_source = result.get("RequestedIdentity").split("@")[0][
        len(SOURCE_PREFIX) :
    ]
    if not SOURCE_CHECK.match(requested_source):
        current_app.logger.debug(
            "The requested source name was {}, which is invalid.".format(
                requested_source
            )
        )
        return error(
            "The source name must be composed of only alphabetical characters (A-Z, a-z), digits (0-9), and underscores (_). It may not begin with a digit.",
            400,
        )

    requested_authorizations = set(result.get("LimitAuthorization").split(","))
    if not requested_authorizations.issubset(ALLOWED_AUTHORIZATIONS):
        return error(
            "The requested token must be limited to the authorizations {}; but you requested {}.".format(
                ", ".join(ALLOWED_AUTHORIZATIONS), ", ".join(requested_authorizations)
            ),
            400,
        )

    try:
        allowed_sources = get_sources(user_id)
    except ConfigurationError:
        return error(
            "Server configuration error. Please contact the administrators.", 500
        )

    current_app.logger.debug(
        "The allowed sources for user {} are {}".format(user_id, allowed_sources)
    )

    if not allowed_sources:
        return error(
            "User {} does not have any sources they are allowed to manage!".format(
                user_id
            ),
            403,
        )

    found_requested_identity = False
    for source in allowed_sources:
        identity = "{}{}@{}".format(SOURCE_PREFIX, source, SOURCE_POSTFIX)
        if identity == result.get("RequestedIdentity"):
            found_requested_identity = True
            break

    if not found_requested_identity:
        return error(
            "The requested source ({}) was not in the list of allowed sources for user {} ({})".format(
                requested_source, user_id, ", ".join(allowed_sources),
            ),
            403,
        )

    try:
        approve_token_request(request_id)
    except CondorToolException:
        current_app.logger.exception("Error while approving token request.")
        return error(
            "Was not able to approve token request. Please try again or contact the administrators.",
            400,
        )

    context = {"source": requested_source, "collector": current_app.config["COLLECTOR"]}
    return make_response(render_template("code_submit_success.html", **context))


def error(info, status_code):
    context = {"info": info}
    return make_response(
        render_template("code_submit_failure.html", **context), status_code
    )


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
