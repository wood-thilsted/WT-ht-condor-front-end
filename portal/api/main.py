from flask import (
    Blueprint
)

from .freshdesk import freshdesk_api_bp

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api/v1"
)

api_bp.register_blueprint(freshdesk_api_bp)

