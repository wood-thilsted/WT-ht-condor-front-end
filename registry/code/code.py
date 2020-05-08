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


@code_bp.route("/code", methods=["GET", "POST"])
def code():
    if request.method == "POST":
        return code_submit()

    response = make_response(render_template("code.html"))
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none';"
    return response


def code_submit():
    if "code" not in request.form:
        context = {"info": "The code parameter is missing"}
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    user_id_env_var = current_app.config.get("USER_ID_ENV_VAR", None)
    if not user_id_env_var:
        context = {"info": "Server configuration error"}
        make_response(render_template("code_submit_failure.html", **context), 500)

    osgid = request.environ.get(user_id_env_var, None)
    if not osgid:
        context = {"info": "Unknown user"}
        make_response(render_template("code_submit_failure.html", **context), 401)

    try:
        result = fetch_tokens(request.form.get("code"), current_app.config)
    except CondorToolException as cte:
        context = {"info": str(cte)}
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    if not result:
        context = {"info": "Request %s is unknown" % request.form.get("code")}
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )
    result = result[0]

    authz = result.get("LimitAuthorization")
    if authz != "ADVERTISE_SCHEDD":
        context = {
            "info": "Token must be limited to the ADVERTISE_SCHEDD authorization"
        }
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    allowed_identity = user_id_to_token_id(osgid)
    if not allowed_identity:
        context = {"info": "User not associated with any known token identity"}
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    found_requested_identity = False
    for hostname in allowed_identity:
        identity = hostname + "@users.htcondor.org"
        if identity == result.get("RequestedIdentity"):
            found_requested_identity = True
            break

    if not found_requested_identity:
        context = {
            "info": "Requested identity (%s) not in the list of allowed CEs (%s)"
            % (result.get("RequestedIdentity"), ", ".join(allowed_identity))
        }
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    try:
        approve_token(request.form.get("code"), current_app.config)
    except CondorToolException as cte:
        context = {
            "info": "Token must be limited to the ADVERTISE_SCHEDD authorization"
        }
        return make_response(
            render_template("code_submit_failure.html", **context), 400
        )

    context = {"info": "Request approved."}
    response = make_response(render_template("code_submit.html", **context))
    return response


def user_id_to_token_id(osgid):
    """
    Map a given OSG ID to a list of authorized CEs they can
    register
    """
    # TODO: Here, we need to create a mapping from CILogon IDs to authorized CEs.
    if osgid == "OSG1000001":
        return ["hcc-briantest7.unl.edu"]


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
