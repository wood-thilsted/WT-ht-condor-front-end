from logging.config import dictConfig
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.append(HERE)
logdir = os.path.join(HERE, "logs")
if not os.path.exists(logdir):
    logdir = "/var/log/condor"

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(levelname)s] %(module)s:%(lineno)s ~ %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "default",
                "stream": "ext://flask.logging.wsgi_errors_stream",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["wsgi"]},
    }
)


from portal import create_app

application = create_app()
