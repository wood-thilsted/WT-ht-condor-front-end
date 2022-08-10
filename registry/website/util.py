# General utility functions

from flask import current_app
import requests


def verify_captcha(user_response: str):

    response = requests.post("https://hcaptcha.com/siteverify",
                  data={
                      'sitekey': current_app.config["H_CAPTCHA_SITEKEY"],  # Optional
                      'secret': current_app.config["H_CAPTCHA_SECRET"],
                      'response': user_response
                  })

    return response.json()['success']
