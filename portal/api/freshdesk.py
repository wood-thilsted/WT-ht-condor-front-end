import json
import logging
import requests
from flask import (
    Blueprint,
    current_app,
    request,
    make_response
)

from portal.website.util import verify_captcha

from .models.response import OkResponse, ErrorResponse

freshdesk_api_bp = Blueprint(
    "freshdesk_api",
    __name__,
    url_prefix="/freshdesk"
)

class FreshDeskAPI:
    """
    Minimal wrapper for FreshDesk's API. ( Copied from HARBORAPI )

    All calls will be made using the credentials provided to the constructor.
    """

    def __init__(self):

        self.session = requests.Session()

        self.base_url = current_app.config["FRESHDESK_API_URL"]
        self.api_key = current_app.config["FRESHDESK_API_KEY"]

        self.log = logging.getLogger(__name__)

    def _renew_session(self):
        if self.session:
            self.session.close()
        self.session = requests.Session()

    def _request(self, method, url, **kwargs):
        """
        Logs and sends an HTTP request.

        Keyword arguments are passed through unmodified to the ``requests``
        library's ``request`` method. If the response contains a status code
        indicating failure, the response is still returned. Other failures
        result in an exception being raised.
        """
        if self.api_key:
            if "auth" not in kwargs:
                kwargs["auth"] = (self.api_key, "X")

        self.log.info("%s %s", method.upper(), url)

        try:
            r = self.session.request(method, url, **kwargs)
        except requests.RequestException as exn:
            self.log.exception(exn)
            raise

        try:
            r.raise_for_status()
        except requests.HTTPError as exn:
            self.log.debug(exn)

        return r

    def _post(self, route, **kwargs):
        """
        Logs and sends an HTTP POST request for the given route.
        """
        self._renew_session()

        return self._request("POST", f"{self.base_url}{route}", **kwargs)

    def create_ticket(
            self,
            name: str,
            email: str,
            subject: str,
            group_id: int,
            description: str,
            priority: int,
            status: int,
            type: str,
            **kwargs
    ) -> requests.Response:
        """
        Create a ticket
        """

        data = json.dumps({
            'name': name,
            'email': email,
            'subject': subject,
            'group_id': group_id,
            'description': description,
            'priority': priority,
            'status': status,
            'type': type,
            **kwargs
        })

        headers = {"Content-Type": "application/json"}

        return self._post(f"/api/v2/tickets", data=data, headers=headers)

    def create_ospool_ticket(
            self,
            name: str,
            email: str,
            description: str
    ):
        ticket_data = {
            "name": name,
            "email": email,
            "description": description,
            "subject": "OSPool User - Account Creation",
            "group_id": 12000006347,  # Actual Value 5000247959
            "priority": 1,
            "status": 2,
            "type": "Other"  # Actual value User Facilitation-Account or login
        }

        return self.create_ticket(**ticket_data)


@freshdesk_api_bp.route("/ticket", methods=["POST"])
def create_ticket():
    """Endpoint for creating a ticket in Freshdesk"""

    if not verify_captcha(request.json['h-captcha-response']["value"]):
        return make_response({'error': "You did not complete the h_captcha"}, 403)

    json = request.json

    # Grab the standard information
    email = json["email"]['value']
    name = json["full-name"]['value']

    # Delete extraneous information to parse the description
    del json['email']
    del json['full-name']
    del json['h-captcha-response']
    del json['g-recaptcha-response']

    # Grab the description
    description = ""
    for key in json.keys():
        description += f"<h3>\n{json[key]['label']}\n</h3>\n"
        description += f"<p>\n{json[key]['value']}\n</p>\n"

    response = FreshDeskAPI().create_ospool_ticket(name=name, email=email, description=description)

    return make_response(response.json(), response.status_code)

