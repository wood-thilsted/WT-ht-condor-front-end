from flask import Flask
import os

from registry.index import index_bp
from registry.api import api_bp

from registry.template_filters import contact_us

BLUEPRINTS = [index_bp, api_bp]
CONTEXT_PROCESSORS = []
TEMPLATE_FILTERS = [contact_us]

if os.path.exists("config.py"):
  HERE = os.getcwd() + "/"
else:
  HERE = os.path.dirname(__file__)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_pyfile(
            os.path.join(os.path.dirname(HERE), "config.py"), silent=True
        )
    else:
        app.config.update(test_config)

    with app.app_context():
        for bp in BLUEPRINTS:
            app.register_blueprint(bp)

        for cp in CONTEXT_PROCESSORS:
            app.context_processor(cp)

        for tf in TEMPLATE_FILTERS:
            app.add_template_filter(tf)

    app.logger.debug("Created!")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=9618)
