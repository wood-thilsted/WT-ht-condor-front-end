from flask import Markup


def contact_us(text):
    return Markup('<a href="{target}">{text}</a>'.format(target="#", text=text))
