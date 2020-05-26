from flask import Blueprint, make_response, render_template, current_app

from ..sources import get_user_id, get_sources
from ..exceptions import ConfigurationError

install_bp = Blueprint(
    "connect",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/connect",
)


@install_bp.route("/connect", methods=["GET"])
def install():
    try:
        user_id = get_user_id()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_id)

    install_commands = {
        source: "bash install_htcondor.sh -c {} -n {} -d {}".format(
            current_app.config["COLLECTOR"], source, current_app.config["DEFAULT_DATA_DIRECTORY"]
        )
        for source in sources
    }

    context = {"install_commands": install_commands}

    response = make_response(render_template("install.html", **context))
    return response
