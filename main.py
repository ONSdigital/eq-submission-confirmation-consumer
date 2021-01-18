# pylint: disable=superfluous-parens
import os
from typing import Dict, Tuple
from uuid import UUID

import simplejson as json
from flask import Request
from notifications_python_client import __version__
from notifications_python_client.authentication import create_jwt_token
from requests import Session
from requests.exceptions import RequestException

session = Session()


NOTIFY_API_KEY = os.environ["NOTIFY_API_KEY"]

template_id_mapping = {
    ("HH", "Eng", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("HH", "Wls", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("HH", "Wls", "cy"): "755d73d1-0cb6-4f2f-95e9-857a2ad071bb",
    ("HH", "Nir", "en"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HH", "Nir", "ga"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HH", "Nir", "eo"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HI", "Eng", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("HI", "Wls", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("HI", "Wls", "cy"): "1001ac43-093d-425c-ac7d-68df5147c603",
    ("HI", "Nir", "en"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("HI", "Nir", "ga"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("HI", "Nir", "eo"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("CE", "Eng", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("CE", "Wls", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("CE", "Wls", "cy"): "e4a4ebea-fcc8-463b-8686-5b8a7320f089",
}


# pylint: disable=too-many-return-statements
def notify(request: Request) -> Tuple[str, int]:
    if not request.method == "POST":
        return "Method not allowed", 405

    if not (data := request.json):
        return "Missing notification request data", 422

    if not (form_type := data.get("form_type")):
        return "Missing form_type identifier", 422

    if not (language_code := data.get("language_code")):
        return "Missing language_code identifier", 422

    if not (region_code := data.get("region_code")):
        return "Missing region_code identifier", 422

    template_id = template_id_mapping.get(
        (form_type, language_code, region_code), os.getenv("NOTIFY_TEST_TEMPLATE_ID")
    )

    if not template_id:
        return "No template id selected", 422

    data_fields = ("email_address", "personalisation")
    return send_email(
        NOTIFY_API_KEY, {key: data.get(key) for key in data_fields}, template_id
    )


def send_email(api_key: str, data: Dict, template_id: str) -> Tuple[str, int]:
    service_id = api_key[-73:-37]
    api_key = api_key[-36:]

    if not is_valid_uuid(service_id):
        return "Service ID is not a valid uuid", 422

    if not is_valid_uuid(api_key):
        return "API key is not a valid uuid", 422

    api_token = create_jwt_token(api_key, service_id)

    session.headers.update(
        {
            "Content-type": "application/json",
            "Authorization": f"Bearer {api_token}",
            "User-agent": f"NOTIFY-API-PYTHON-CLIENT/{__version__}",
        }
    )
    kwargs = json.dumps({"template_id": template_id, **data})

    try:
        response = session.post(
            "https://api.notifications.service.gov.uk/v2/notifications/email",
            kwargs,
        )
        response.raise_for_status()
    except RequestException as error:
        error_message = error.response.json()["errors"][0]
        status_code = error.response.status_code
        entry = dict(
            severity="ERROR",
            status_code=status_code,
            message=f"Notify request failed: {error_message}",
        )
        print(entry)
        return "Notify request failed", error.response.status_code

    if response.status_code == 204:
        return "No content", 204

    try:
        return response.json()
    except ValueError:
        return "Notify JSON response object failed decoding", 503


def is_valid_uuid(identifier: str) -> bool:
    try:
        UUID(identifier, version=4)
    except ValueError:
        return False

    return True
