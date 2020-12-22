from flask import Blueprint, make_response, render_template, current_app

from ..sources import get_user_info, get_sources
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
        user_info = get_user_info()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_info)

    context = {"sources": sources}

    response = make_response(render_template("connect.html", **context))
    return response


@install_bp.route("/connect/docker", methods=["GET"])
def docker():
    try:
        user_info = get_user_info()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_info)

    install_commands = {
        source: "docker run -v $PWD/tokens:/etc/condor/tokens.d opensciencegrid/open-science-pool-registry:fresh register.py --local-dir $PWD/tokens --host {}".format(
            source
        )
        for source in sources
    }

    context = {"sources": sources, "install_commands": install_commands}

    response = make_response(render_template("docker.html", **context))
    return response


@install_bp.route("/connect/kubernetes", methods=["GET"])
def kubernetes():
    try:
        user_info = get_user_info()
    except ConfigurationError:
        return "Server configuration error", 500

    sources = get_sources(user_info)

    install_commands = {
        source: "bash install_htcondor.sh -c {} -n {} -d {} -x Docker".format(
            current_app.config["COLLECTOR"],
            source,
            current_app.config["DEFAULT_DATA_DIRECTORY"],
        )
        for source in sources
    }

    context = {"sources": sources, "install_commands": install_commands}

    response = make_response(render_template("kubernetes.html", **context))
    return response
