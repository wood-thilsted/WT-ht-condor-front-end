from flask import Flask
import flask_assets
import os

from registry.website import website_bp
from registry.api import api_bp

from registry.template_filters import contact_us

BLUEPRINTS = [website_bp, api_bp]
CONTEXT_PROCESSORS = []
TEMPLATE_FILTERS = [contact_us]

if os.path.exists("config.py"):
  HERE = os.getcwd() + "/"
else:
  HERE = os.path.dirname(__file__)

def define_assets(app) -> None:
    assets = flask_assets.Environment(app)
    assets.url = app.static_url_path
    assets.config['SECRET_KEY'] = 'secret!'
    assets.config['PYSCSS_LOAD_PATHS'] = assets.load_path
    assets.config['PYSCSS_STATIC_URL'] = assets.url
    assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
    assets.config['PYSCSS_ASSETS_URL'] = assets.url
    assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory
    assets.cache = False

    css_main = flask_assets.Bundle(
        "scss/main.scss",
        filters="libsass",
        output="css/main.css"
    )

    assets.register("css_main", css_main)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_pyfile(
            os.path.join(os.path.dirname(HERE), "config.py"), silent=True
        )
    else:
        app.config.update(test_config)

    define_assets(app)

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
    app.run(port=9618, debug=True)
