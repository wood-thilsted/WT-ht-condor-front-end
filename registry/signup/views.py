import smtplib
import socket
from email.mime.text import MIMEText
from email.utils import getaddresses

from flask import Blueprint, request, current_app, make_response, render_template

from ..sources import get_user_id, is_valid_source_name
from ..exceptions import ConfigurationError

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


EXPECTED_FORM_KEYS = {"contact", "email", "source"}


@signup_bp.route("/signup", methods=["POST"])
def signup_post():
    got_keys = set(request.form.keys())
    if got_keys != EXPECTED_FORM_KEYS:
        return error(
            "A form parameter was missing. Got {}, expected {}.".format(
                got_keys, EXPECTED_FORM_KEYS
            ),
            400,
        )

    source = request.form["source"]
    if not is_valid_source_name(source):
        return error(
            'The source name you entered ("{}") is not valid. The source name must be composed of only alphabetical characters (A-Z, a-z), digits (0-9), and underscores (_). It may not begin with a digit.'.format(
                source
            ),
            400,
        )

    contact = request.form["contact"]

    try:
        admin_emails = current_app.config["ADMIN_EMAILS"]
    except KeyError:
        current_app.logger.error(
            "Invalid internal configuration: ADMIN_EMAILS is not set"
        )
        return error("Server configuration error", 500)

    try:
        user_id = get_user_id()
    except ConfigurationError:
        return error("Server configuration error", 500)

    if user_id is None:
        return error("Unknown user", 401)

    try:
        hostname = socket.gethostname()
        email = request.form["email"]
        msg = MIMEText(
            """
A new user has signed up for the HTPhenotyping system.  

Contact information includes:
- Identity: {user_id}
- Contact Name: {contact}
- Preferred email: {email}
- Source name: {source}

If approved, please add the user data to the following repository:
    https://github.com/HTPhenotyping/sources
""".format(
                contact=contact, user_id=user_id, email=email, source=source,
            )
        )
        msg["Subject"] = "New HTPheno sign-up from {contact} ({user})".format(
            contact=contact, user=user_id
        )
        msg["From"] = "HTPheno Webapp <donotreply@{}>".format(hostname)
        msg["To"] = admin_emails
    except:
        current_app.logger.exception("Failed to construct sign up email")
        return error("Internal server error; sign up failed. Please try again.", 500)

    current_app.logger.info("Signup email contents: %s", msg.as_string())
    try:
        server = smtplib.SMTP("localhost")
        emails = [i[1] for i in getaddresses([msg["To"]])]
        server.sendmail("donotreply@{}".format(hostname), emails, msg.as_string())
        server.quit()
    except:
        current_app.logger.exception("Failed to send sign up email")
        return error("Internal server error; sign up failed. Please try again.", 500)

    context = {"email": email}
    return make_response(render_template("signup_submit_success.html", **context))


def error(info, status_code):
    context = {"info": info}
    return make_response(
        render_template("signup_submit_failure.html", **context), status_code
    )
