from flask import (
    Blueprint,
    request,
    current_app,
    make_response,
    render_template,
    url_for,
)

from ..mail import send_mail_to_admins
from ..sources import (
    get_user_info,
    is_valid_source_name,
)
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
    response = make_response(render_template("signup.html"))
    return response


EXPECTED_SIGNUP_KEYS = {"contact", "email"}


@signup_bp.route("/signup", methods=["POST"])
def signup_post():
    got_keys = set(request.form.keys())
    if got_keys != EXPECTED_SIGNUP_KEYS:
        return error(
            "A form parameter was missing. Got {}, expected {}.".format(
                got_keys, EXPECTED_SIGNUP_KEYS
            ),
            "signup",
            400,
        )

    contact = request.form["contact"]
    email = request.form["email"]

    try:
        user_id = get_user_info()
    except ConfigurationError:
        return error("Server configuration error", "signup", 500)

    if user_id is None:
        return error("Unknown user", "signup", 401)

    subject = "New HT Phenotyping signup request from {contact} ({user})".format(
        contact=contact, user=user_id
    )
    text = """\
        A new user has signed up for the HT Phenotyping service.
        
        Details:
        - Name: {user_id}
        - Contact Name: {contact}
        - Contact Email: {email}
        
        If approved, please add the user's data to the sources repository:
        https://github.com/HTPhenotyping/sources
        """.format(
        contact=contact, user_id=user_id, email=email,
    )

    try:
        send_mail_to_admins(
            text, subject,
        )
    except:
        current_app.logger.exception("Failed to send sign up email")
        return error(
            "Internal server error; sign up failed. Please try again.", "signup", 500
        )

    context = {
        "email": email,
        "info": 'Now that you\'ve signed up, you can <strong><a href="{}">register data sources</a></strong>.'.format(
            url_for("signup.register_get")
        ),
        "which": "signup",
    }
    return make_response(render_template("submit_success.html", **context))


@signup_bp.route("/register", methods=["GET"])
def register_get():
    try:
        user_id = get_user_info()
    except ConfigurationError:
        return error(
            "Server configuration error. Please contact the administrators.",
            "registration",
            500,
        )

    if user_id is not None:
        context = {"contact": user_id.get("email", "(Unknown email)"), "name": user_id.get("name", "(Unknown name)")}
    else:
        context = {}

    response = make_response(render_template("register.html", **context))
    return response


EXPECTED_REGISTER_KEYS = {"email", "source"}


@signup_bp.route("/register", methods=["POST"])
def register_post():
    got_keys = set(request.form.keys())
    if got_keys != EXPECTED_REGISTER_KEYS:
        return error(
            "A form parameter was missing. Got {}, expected {}.".format(
                got_keys, EXPECTED_REGISTER_KEYS
            ),
            "registration",
            400,
        )

    source = request.form["source"]
    if not is_valid_source_name(source):
        return error(
            'The source name you entered ("{}") is not valid. The source name must be composed of only alphabetical characters (A-Z, a-z), digits (0-9), and underscores (_). It may not begin with a digit.'.format(
                source
            ),
            "registration",
            400,
        )

    email = request.form["email"]

    try:
        user_id = get_user_info()
    except ConfigurationError:
        return error("Server configuration error", "registration", 500)

    if user_id is None:
        return error("Unknown user", "registration", 401)

    subject = "New HT Phenotyping source registration request from {user}".format(
        contact_email=email, user=user_id
    )
    text = """\
        A new data source has been registered for the HT Phenotyping service.
        
        Details:
        - Contact Email: {email}
        - Source Name: {source}
        
        If approved, please add the sources's data to the sources repository:
        https://github.com/HTPhenotyping/sources
        """.format(
        email=email, user_id=user_id, source=source,
    )

    try:
        send_mail_to_admins(
            text, subject,
        )
    except:
        current_app.logger.exception("Failed to send sign up email")
        return error(
            "Internal server error; sign up failed. Please try again.",
            "registration",
            500,
        )

    context = {"email": email, "which": "registration"}
    return make_response(render_template("submit_success.html", **context))


def error(info, which, status_code):
    context = {"info": info, "which": which}
    return make_response(render_template("submit_failure.html", **context), status_code)
