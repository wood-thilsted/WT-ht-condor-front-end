import subprocess
import os
import json

from flask import Blueprint, request, current_app, make_response, render_template

from ..sources import get_user_info, get_access_point_fqdns, get_execution_endpoint_fqdns, is_valid_source_name
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


SOURCE_PREFIX = "RESOURCE-"
SOURCE_POSTFIX = "flock.opensciencegrid.org"
BASE_ALLOWED_AUTHORIZATIONS = {"READ", "ADVERTISE_MASTER"}
AP_ALLOWED_AUTHORIZATIONS = {"ADVERTISE_SCHEDD"}
EE_ALLOWED_AUTHORIZATIONS = {"ADVERTISE_STARTD"}


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
        user_id = get_user_info()
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

    split_identity = result.get("RequestedIdentity").rsplit("@", 1)
    if len(split_identity) != 2:
        current_app.logger.debug(
            "The requested identity was {}, which is invalid (missing domain).".format(
                result.get("RequestedIdentity")
            )
        )
        return error(
            "The requested identity is invalid; it must be of the form 'user@domain'",
            400
        )

    requested_identity, requested_domain = split_identity

    if requested_domain != SOURCE_POSTFIX:
        current_app.logger.debug(
            "The requested identity was {}, which is invalid (wrong domain).".format(
                result.get("RequestedIdentity")
            )
        )
        return error(
            "The requested identity is invalid; it must use domain {}.".format(
                SOURCE_POSTFIX
            ),
            400
        )

    if not requested_identity.startswith(SOURCE_PREFIX):
        current_app.logger.debug(
            "The requested identity was {}, which is invalid (wrong prefix).".format(
                result.get("RequestedIdentity")
            )
        )
        return error(
            "The requested identity is invalid; it must start with prefix {}.".format(
                SOURCE_PREFIX
            ),
            400
        )

    requested_source = requested_identity[len(SOURCE_PREFIX):]
    if not is_valid_source_name(requested_source):
        current_app.logger.debug(
            "The requested source name was {}, which is invalid.".format(
                requested_source
            )
        )
        return error(
            "The source name must be composed of only alphabetical characters (A-Z, a-z), digits (0-9), and underscores (_). It may not begin with a digit.",
            400,
        )

    allowed_ap = []
    allowed_ee = []
    allowed_sources = []
    try:
        allowed_ap = get_access_point_fqdns(user_id)
        allowed_ee = get_execution_endpoint_fqdns(user_id)
        allowed_sources = allowed_ap + allowed_ee
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

    requested_fqdn = result.get("RequestedIdentity").lstrip(SOURCE_PREFIX).rstrip(f'@{SOURCE_POSTFIX}')
    if requested_fqdn not in allowed_sources:
        return error(
            "The requested source ({}) was not in the list of allowed sources for user {} ({})".format(
                requested_source, user_id, ", ".join(allowed_sources),
            ),
            403,
        )

    def verify_requested_authz(requested, allowed):
        if not requested.issubset(allowed):
            return error(
                "The requested token must be limited to the authorizations {}; but you requested {}.".format(
                    ", ".join(allowed), ", ".join(requested)
                ),
                400,
            )

    requested_authorizations = set(result.get("LimitAuthorization").split(","))
    if requested_fqdn in allowed_ap:
        verify_requested_authz(requested_authorizations,
                               set.union(BASE_ALLOWED_AUTHORIZATIONS, AP_ALLOWED_AUTHORIZATIONS))
    elif requested_fqdn in allowed_ee:
        verify_requested_authz(requested_authorizations,
                               set.union(BASE_ALLOWED_AUTHORIZATIONS, EE_ALLOWED_AUTHORIZATIONS))

    try:
        approve_token_request(request_id)
    except CondorToolException:
        current_app.logger.exception("Error while approving token request.")
        return error(
            "Was not able to approve token request. Please try again or contact the administrators.",
            400,
        )
    current_app.logger.info("Approved token request: approver_id={}, approver_name={}, approver_email={}, "
        "req_id={}, requester_identity={}, authz_limits={}, requester_ip={}, token_identity={}, "
        "request_client_id={}".format(
            user_id.get("id"), user_id.get("name"), user_id.get("email"),
            request_id, result.get("AuthenticatedIdentity"), result.get("LimitAuthorization"),
            result.get("PeerLocation"), result.get("RequestedIdentity"), result.get("ClientId")
        )
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
    args = [binary, "-pool", current_app.config["COLLECTOR"], "-reqid", str(request_id), "-json"]

    current_app.logger.error("Running {}".format(" ".join(args)))

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
    args = [binary, "-pool", current_app.config["COLLECTOR"], "-reqid", str(request_id)]

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
    req_environ["_condor_SEC_CLIENT_AUTHENTICATION_METHODS"] = "IDTOKENS"
    req_environ["_condor_SEC_CLIENT_ENCRYPTION"] = "REQUIRED"
    req_environ["_condor_SEC_TOKEN_DIRECTORY"] = "/etc/condor/tokens.d"

    return req_environ
