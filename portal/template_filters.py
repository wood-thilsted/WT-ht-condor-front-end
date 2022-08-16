from flask import Markup, current_app


def contact_us(text):
    return Markup(
        '<a href="mailto:{target}">{text}</a>'.format(
            target=current_app.config["SUPPORT_EMAIL"], text=text
        )
    )
