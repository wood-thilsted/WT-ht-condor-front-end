from flask import Blueprint, make_response, render_template, current_app, request

from ..sources import get_user_id, get_sources, get_contact_email, is_signed_up
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
    except ConfigurationError:
        return "Server configuration error", 500

    if not is_signed_up(user_id):
        context = {"identity": user_id, "signed_up": False}
        return make_response(render_template("account.html", **context))

    contact = get_contact_email(user_id)
    sources = get_sources(user_id)

    context = {
        "identity": user_id,
        "signed_up": True,
        "contact": contact,
        "sources": sources,
    }
    return make_response(render_template("account.html", **context))
