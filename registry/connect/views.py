from flask import Blueprint, make_response, render_template

install_bp = Blueprint(
    "connect",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/connect",
)


@install_bp.route("/connect", methods=["GET"])
def install():
    response = make_response(render_template("install.html"))
    return response
