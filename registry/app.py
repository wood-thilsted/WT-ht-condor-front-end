from flask import Flask
import flask_assets
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

def define_assets(app: flask.Flask) -> None:
    assets = flask_assets.Environment(app)
    assets.url = app.static_url_path

    if app.config["DEBUG"]:
        assets.config["LIBSASS_STYLE"] = "nested"
        js_main = flask_assets.Bundle(
            "js/bootstrap.js",
            output="assets/js/main.js",
        )
        js_registration = flask_assets.Bundle(
            "js/registration.js",
            output="assets/js/registration.js",
        )
        js_account = flask_assets.Bundle(
            "js/account.js",
            output="assets/js/account.js",
        )
    else:
        ## Assume that a production webserver cannot write these files.
        assets.auto_build = False
        assets.cache = False
        assets.manifest = False

        assets.config["LIBSASS_STYLE"] = "compressed"
        js_main = flask_assets.Bundle(
            "js/bootstrap.js",
            filters="rjsmin",
            output="assets/js/main.min.js",
        )
        js_registration = flask_assets.Bundle(
            "js/registration.js",
            filters="rjsmin",
            output="assets/js/registration.min.js",
        )
        js_account = flask_assets.Bundle(
            "js/account.js",
            filters="rjsmin",
            output="assets/js/account.min.js",
        )

    css = flask_assets.Bundle(
        "style.scss",
        filters="libsass",
        output="assets/css/style.css",
    )

    assets.register("soteria_js_main", js_main)
    assets.register("soteria_js_registration", js_registration)
    assets.register("soteria_js_account", js_account)
    assets.register("soteria_css", css)


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
