try:  # py3
    from urllib.parse import urlencode
except ImportError:  # py2
    from urllib import urlencode

from flask import (
    Blueprint,
    request,
    current_app,
    make_response,
    render_template,
    redirect,
    url_for,
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
        return
    params = {"logout": url_for("index.index", _external=True)}
    # TODO: build the url using urllib
    return redirect("{}?{}".format(redirect_uri, urlencode(params)))
