import re

try:  # py3
    from configparser import ConfigParser
except ImportError:  # py2
    from ConfigParser import ConfigParser

from flask import current_app, request

from .exceptions import ConfigurationError


def get_user_id():
    try:
        user_id_env_var = current_app.config["USER_ID_ENV_VAR"]
    except KeyError:
        msg = "Config variable USER_ID_ENV_VAR not set; this should be set to the name of the environment variable that holds the user's identity (perhaps REMOTE_USER ?)"
        current_app.logger.error(msg)
        raise ConfigurationError(msg)

    current_app.logger.debug(
        "Will read user ID from request environment variable {}".format(user_id_env_var)
    )

    user_id = request.environ.get(user_id_env_var, None)
    current_app.logger.debug("User ID is {}".format(user_id))

    return user_id


def is_signed_up(user_id):
    return any(user_id == entry["name"] for entry in parse_humans_file())


def get_sources(user_id):
    """
    Map a given user ID to a list of sources they are authorized to administrate.
    """
    names_to_sources = {
        entry["name"]: entry["sources"].split() for entry in parse_humans_file()
    }
    return names_to_sources.get(user_id, [])


def get_contact_email(user_id):
    names_to_contacts = {entry["name"]: entry["email"] for entry in parse_humans_file()}
    return names_to_contacts.get(user_id, None)


def parse_humans_file():
    try:
        humans_file = current_app.config["HUMANS_FILE"]
    except KeyError:
        msg = "Config variable HUMANS_FILE not set; this should be set to the path of the file containing the information on humans."
        current_app.logger.error(msg)
        raise ConfigurationError(msg)

    config = ConfigParser()
    config.read(humans_file)

    entries = config_to_entries(config)

    return entries


def config_to_entries(config):
    entries = []
    for section in config.sections():
        entry = {}
        for option in config.options(section):
            entry[option] = config.get(section, option)

        entries.append(entry)

    return entries


SOURCE_CHECK = re.compile(r"^[a-zA-Z]\w*$")


def is_valid_source_name(source_name):
    return bool(SOURCE_CHECK.match(source_name))
