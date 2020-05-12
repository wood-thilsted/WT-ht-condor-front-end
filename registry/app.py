import os

from flask import Flask

from .index import index_bp
from .code import code_bp
from .signup import signup_bp

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
        app.register_blueprint(index_bp)
        app.register_blueprint(code_bp)
        app.register_blueprint(signup_bp)

    app.logger.debug("Created!")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
