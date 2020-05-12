import smtplib
import socket
from email.mime.text import MIMEText
from email.utils import getaddresses

from flask import Blueprint, request, current_app, make_response, render_template

signup_bp = Blueprint(
    "signup",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/signup",
)


@signup_bp.route("/signup", methods=["GET"])
def signup_get():
    response = make_response(render_template("signup_submit.html"))
    return response


@signup_bp.route("/signup", methods=["POST"])
def signup_post():
    for varname in ["contact", "email", "source", "sourcePath"]:
        if varname not in request.form:
            return error("The '{}' parameter is missing".format(varname), 400)

    try:
        admin_emails = current_app.config["ADMIN_EMAILS"]
    except KeyError:
        current_app.logger.error(
            "Invalid internal configuration: ADMIN_EMAILS parameter is not set"
        )
        return error("Server configuration error", 500)

    try:
        user_id_env_var = current_app.config["USER_ID_ENV_VAR"]
    except KeyError:
        current_app.logger.error(
            "Config variable USER_ID_ENV_VAR not set; this should be set to the name of the environment variable that holds the user's identity (perhaps REMOTE_USER ?)"
        )
        return error("Server configuration error", 500)

    user_id = request.environ.get(user_id_env_var, None)
    current_app.logger.debug("User ID is {}".format(user_id))
    if not user_id:
        return error("Unknown user", 401)

    try:
        hostname = socket.gethostname()
        msg = MIMEText(
            """
A new user has signed up for the HTPhenotyping system.  

Contact information includes:
- Name: {contact}
- User name: {user}
- Preferred email: {email}
- Source name: {source}
- Source path: {sourcePath}

If approved, please add the user data to the following repository:
    https://github.com/HTPhenotyping/sources
""".format(
                contact=request.form["contact"],
                user=user_id,
                email=request.form["email"],
                source=request.form["source"],
                sourcePath=request.form["sourcePath"],
            )
        )
        msg["Subject"] = "New HTPheno sign-up from {contact} ({user})".format(
            contact=request.form["contact"], user=user_id
        )
        msg["From"] = "HTPheno Webapp <donotreply@{}>".format(hostname)
        msg["To"] = admin_emails
    except:
        current_app.logger.exception("Failed to construct email message")
        return error("Internal error when generating email to administrators", 500)

    current_app.logger.info("Signup email contents: %s", msg.as_string())
    try:
        server = smtplib.SMTP("localhost")
        emails = [i[1] for i in getaddresses([msg["To"]])]
        server.sendmail("donotreply@{}".format(hostname), emails, msg.as_string())
        server.quit()
    except:
        current_app.logger.exception("Failed to send sign-up email")
        return error("Failed to send sign-up email to server admins", 500)

    return make_response(render_template("signup_submit_success.html"))


def error(info, status_code):
    context = {"info": info}
    return make_response(
        render_template("signup_submit_failure.html", **context), status_code
    )
