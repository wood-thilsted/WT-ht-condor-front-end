from .sources import get_user_id, get_name
from .exceptions import ConfigurationError


def inject_user_name():
    try:
        user_id = get_user_id()
    except ConfigurationError:
        return {"user_name": None}

    return {"user_name": get_name(user_id)}
