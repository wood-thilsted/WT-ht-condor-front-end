import json
import logging
import requests
from flask import (
    Blueprint,
    current_app,
    request
)

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

        self.base_url = current_app.config["FRESH_DESK_API_URL"]
        self.api_key = current_app.config["FRESH_DESK_API_KEY"]

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
            name: name,
            email: email,
            subject: subject,
            description: description,
            priority: priority,
            status: status,
            type: type,
            **kwargs
        })

        headers = {"Content-Type": "application/json"}

        return self._post(f"/api/v2/tickets", data=data, headers=headers)


@freshdesk_api_bp.route("/ticket", methods=["POST"])
def create_ticket():
    """Endpoint for creating a ticket in Freshdesk"""

    ticket_data = {
        "name": request.json['name'],
        "email": request.json['email'],
        "description": request.json['description'],
        "subject": "SOTERIA Researcher Application",
        "group_id": 5000247959,
        "priority": 1,
        "status": 2,
        "type": "OSPool User Orientation Application",
        **request.json
    }

    response = FreshDeskAPI().create_ticket(**ticket_data)

    if response.status_code == 200:
        return OkResponse("ok", response.json())

    else:
        return ErrorResponse("error", {
            "code": response.status_code,
            "message": response.text
        })
