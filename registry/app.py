#!/usr/bin/env python3


from pathlib import Path

from flask import Flask

from .code import code_bp

HERE = Path(__file__).parent


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_pyfile(HERE.parent / "config.py", silent=True)
    else:
        app.config.update(test_config)

    with app.app_context():
        app.register_blueprint(code_bp)

        @app.route("/health")
        def health():
            return "Hello!"

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
