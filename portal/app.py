from flask import (
    Flask,
    render_template
)
import flask_assets
import os

from portal.website import website_bp
from portal.api import api_bp

from portal.template_filters import contact_us

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

    if not app.debug:
        assets.cache = False
        assets.manifest = False

    css_main = flask_assets.Bundle(
        "scss/main.scss",
        filters="libsass",
        output="css/main.css"
    )

    assets.register("css_main", css_main)

def load_config(app: Flask, test_config: str) -> None:

    if test_config is None:
        app.config.from_pyfile(
            os.path.join(os.path.dirname(HERE), "config.py"), silent=True
        )
    else:
        app.config.update(test_config)

    for key in [
        "FRESHDESK_API_KEY",
        "H_CAPTCHA_SECRET"
    ]:
        val = os.environ.get(key)
        if val is not None:
            app.config[key] = val


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    load_config(app, test_config)
    define_assets(app)

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template('404.html'), 404

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
