import collections
import subprocess
import os
import json

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


@code_bp.route("/code", methods=["POST"])
def code_post():
    if "code" not in request.form:
        return error("The code parameter is missing", 400)

    user_id_env_var = current_app.config.get("USER_ID_ENV_VAR", None)
    if not user_id_env_var:
        current_app.logger.error(
            "Config variable USER_ID_ENV_VAR not set; this should be set to the name of the environment variable that holds the user's identity (perhaps REMOTE_USER ?)"
        )
        return error("Server configuration error", 500)

    user_id = request.environ.get(user_id_env_var, None)
    if not user_id:
        return error("Unknown user", 401)

    try:
        result = fetch_tokens(request.form.get("code"), current_app.config)
    except CondorToolException as cte:
        return error(str(cte), 400)

    if not result:
        return error("Request {} is unknown".format(request.form.get("code")), 400)
    result = result[0]

    authz = result.get("LimitAuthorization")
    if authz != "ADVERTISE_SCHEDD":
        return error("Token must be limited to the ADVERTISE_SCHEDD authorization", 400)

    allowed_token_ids = valid_token_ids(user_id)
    if not allowed_token_ids:
        return error("User not associated with any known token identity", 400)

    found_requested_identity = False
    for hostname in allowed_token_ids:
        identity = hostname + "@users.htcondor.org"
        if identity == result.get("RequestedIdentity"):
            found_requested_identity = True
            break

    if not found_requested_identity:
        return error(
            "Requested identity ({}) not in the list of allowed CEs ({})".format(
                result.get("RequestedIdentity"), ", ".join(allowed_token_ids)
            ),
            400,
        )

    try:
        approve_token(request.form.get("code"), current_app.config)
    except CondorToolException as cte:
        return error("Token must be limited to the ADVERTISE_SCHEDD authorization", 400)

    context = {"info": "Request approved."}
    response = make_response(render_template("code_submit_success.html", **context))
    return response


def error(info, status_code):
    context = {"info": info}
    return make_response(
        render_template("code_submit_failure.html", **context), status_code
    )


def valid_token_ids(user_id):
    """
    Map a given OSG ID to a list of authorized CEs they canregister
    """
    user_id_token_ids = current_app.config["MAPFILE"]

    return user_id_token_ids.get(user_id, [])


def _parse_mapfile():
    mapfile = current_app.config["MAPFILE"]

    user_to_token_ids = collections.defaultdict(set)
    with open(mapfile) as f:
        for line in f:
            user, token = line.split()
            user_to_token_ids[user].add(token)

    return user_to_token_ids


def fetch_tokens(reqid, config):
    binary = config.get("CONDOR_TOKEN_REQUEST_LIST", "condor_token_request_list")
    pool = config.get("CONDORCE_COLLECTOR")
    args = [binary, "-reqid", str(reqid), "-json"]
    if pool:
        args.extend(["-pool", pool])
    req_environ = dict(os.environ)
    req_environ.setdefault("CONDOR_CONFIG", "/etc/condor-ce/condor_config")
    req_environ["_condor_SEC_CLIENT_AUTHENTICATION_METHODS"] = "TOKEN"
    req_environ["_condor_SEC_TOKEN_DIRECTORY"] = "/etc/condor-ce/webapp.tokens.d"
    process = subprocess.Popen(
        args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=req_environ
    )
    stdout, stderr = process.communicate()
    if process.returncode:
        raise CondorToolException(
            "Failed to list internal requests: {}".format(stderr.decode("utf-8"))
        )
    try:
        json_obj = json.loads(stdout)
    except json.JSONDecodeError:
        raise CondorToolException("Internal error: invalid format of request list")

    return json_obj


def approve_token(reqid, config):
    binary = config.get("CONDOR_TOKEN_REQUEST_APPROVE", "condor_token_request_approve")
    pool = config.get("CONDORCE_COLLECTOR")
    args = [binary, "-reqid", str(reqid)]
    if pool:
        args.extend(["-pool", pool])
    req_environ = dict(os.environ)
    req_environ.setdefault("CONDOR_CONFIG", "/etc/condor-ce/condor_config")
    req_environ["_condor_SEC_CLIENT_AUTHENTICATION_METHODS"] = "TOKEN"
    req_environ["_condor_SEC_TOKEN_DIRECTORY"] = "/etc/condor-ce/webapp.tokens.d"
    process = subprocess.Popen(
        args,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        env=req_environ,
    )
    stdout, stderr = process.communicate(input=b"yes\n")
    if process.returncode:
        raise CondorToolException(
            "Failed to approve request: {}".format(stderr.decode("utf-8"))
        )
