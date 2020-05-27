import smtplib
import socket
from email.mime.text import MIMEText
from email.utils import getaddresses
import textwrap

from flask import current_app

from .exceptions import ConfigurationError


def send_mail_to_admins(body, subject):
    hostname = socket.gethostname()
    admin_emails = get_admin_emails()

    body = textwrap.dedent(body)
    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = "HT Phenotyping Webapp <donotreply@{}>".format(hostname)
    msg["To"] = admin_emails

    current_app.logger.debug(
        'Sending email to {to}. Subject: "{subject}"\nBody:\n{body}'.format(
            to=admin_emails, subject=subject, body=body,
        )
    )

    server = smtplib.SMTP("localhost")
    emails = [i[1] for i in getaddresses([msg["To"]])]
    server.sendmail("donotreply@{}".format(hostname), emails, msg.as_string())
    server.quit()

    current_app.logger.debug("Sent email to {}".format(admin_emails))


def get_admin_emails():
    try:
        return current_app.config["ADMIN_EMAILS"]
    except KeyError:
        msg = "Invalid internal configuration: ADMIN_EMAILS is not set"
        current_app.logger.error(msg)
        raise ConfigurationError(msg)
