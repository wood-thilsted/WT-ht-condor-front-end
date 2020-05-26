from flask import Blueprint, make_response, render_template, current_app, request

from ..sources import get_user_id, get_sources
from ..exceptions import ConfigurationError

account_bp = Blueprint(
    "account",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/account",
)


@account_bp.route("/account", methods=["GET"])
def account_get():
    try:
        user_id = get_user_id()
        sources = get_sources(user_id)
    except ConfigurationError:
        return "Server configuration error", 500

    context = {"identity": user_id, "sources": sources}

    response = make_response(render_template("account.html", **context))
    return response
