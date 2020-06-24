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
def connect():
    try:
        user_id = get_user_id()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_id)

    context = {"sources": sources}

    response = make_response(render_template("connect.html", **context))
    return response


@install_bp.route("/connect/ubuntu-18", methods=["GET"])
def ubuntu_18():
    try:
        user_id = get_user_id()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_id)

    install_commands = {
        source: "bash install_htcondor.sh -c {} -n {} -d {}".format(
            current_app.config["COLLECTOR"],
            source,
            current_app.config["DEFAULT_DATA_DIRECTORY"],
        )
        for source in sources
    }

    context = {"sources": sources, "install_commands": install_commands}

    response = make_response(render_template("ubuntu-18.html", **context))
    return response


@install_bp.route("/connect/macos", methods=["GET"])
def macos():
    try:
        user_id = get_user_id()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_id)

    install_commands = {
        source: "bash install_htcondor.sh -c {} -n {} -d {} -x Docker".format(
            current_app.config["COLLECTOR"],
            source,
            current_app.config["DEFAULT_DATA_DIRECTORY"],
        )
        for source in sources
    }

    context = {"sources": sources, "install_commands": install_commands}

    response = make_response(render_template("macos-docker.html", **context))
    return response
