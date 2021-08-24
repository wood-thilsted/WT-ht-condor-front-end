from flask import Blueprint, make_response, render_template, current_app, request

from ..sources import get_user_info, get_access_point_fqdns, get_execution_endpoint_fqdns, is_signed_up
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
        user_info = get_user_info()
    except ConfigurationError:
        return "Server configuration error", 500

    if not is_signed_up(user_info):
        context = {"user_info": user_info, "signed_up": False}
        return make_response(render_template("account.html", **context))

    sources = get_access_point_fqdns(user_info)
    sources += get_execution_endpoint_fqdns(user_info)

    context = {
        "user_info": user_info,
        "signed_up": True,
        "sources": sources,
    }
    return make_response(render_template("account.html", **context))
