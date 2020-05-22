try:  # py3
    from urllib.parse import urlencode
except ImportError:  # py2
    from urllib import urlencode

from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    redirect,
)

index_bp = Blueprint(
    "index",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/index",
)


@index_bp.route("/")
def index():
    return make_response(render_template("index.html"))


@index_bp.route("/about")
def about():
    return make_response(render_template("about.html"))


@index_bp.route("/health")
def health():
    return "Hello!"


@index_bp.route("/logout")
def logout():
    try:
        redirect_uri = current_app.config["OIDC_REDIRECT_URI"]
    except KeyError:
        current_app.logger.error(
            "Invalid internal configuration: OIDC_REDIRECT_URI is not set"
        )
        return "Error!"
    # TODO: build the urls using urllib; this is pretty gnarly...
    try:
        params = {"logout": "https://" + current_app.config["SERVER_NAME"]}
    except KeyError:
        current_app.logger.error(
            "Invalid internal configuration: SERVER_NAME is not set"
        )
        return "Error!"
    url = "{}?{}".format(redirect_uri, urlencode(params))
    current_app.logger.debug("Redirecting logout to", url)
    return redirect(url)
