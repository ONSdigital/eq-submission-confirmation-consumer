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

NOTIFY_BASE_URL = "https://api.notifications.service.gov.uk/v2"

template_id_mapping = {
    ("HH", "GB-ENG", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("HH", "GB-WLS", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("HH", "GB-WLS", "cy"): "755d73d1-0cb6-4f2f-95e9-857a2ad071bb",
    ("HH", "GB-NIR", "en"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HH", "GB-NIR", "ga"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HH", "GB-NIR", "eo"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("HI", "GB-ENG", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("HI", "GB-WLS", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("HI", "GB-WLS", "cy"): "1001ac43-093d-425c-ac7d-68df5147c603",
    ("HI", "GB-NIR", "en"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("HI", "GB-NIR", "ga"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("HI", "GB-NIR", "eo"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("CE", "GB-ENG", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("CE", "GB-WLS", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("CE", "GB-WLS", "cy"): "e4a4ebea-fcc8-463b-8686-5b8a7320f089",
}

data_fields = ("email_address", "display_address", "tx_id", "questionnaire_id")


def log_entry(**kwargs):
    print(json.dumps(kwargs))


# pylint: disable=too-many-return-statements
def notify(request: Request) -> Tuple[str, int]:
    if not request.method == "POST":
        # Note that Cloud Functions expect serialized JSON
        # to correctly log
        # https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
        msg = "Method not allowed"
        log_entry(severity="ERROR", message=msg)
        return msg, 405

    if not (data := request.json):
        msg = "Missing notification request data"
        log_entry(severity="ERROR", message=msg)
        return msg, 422

    data = request.json["fulfilmentRequest"]

    entry = {
        "tx_id": data.get("tx_id"),
        "questionnaire_id": data.get("questionnaire_id"),
    }

    if not (form_type := data.get("form_type")):
        msg = "Missing form_type identifier"
        log_entry(severity="ERROR", message=msg, **entry)
        return msg, 422

    if not (language_code := data.get("language_code")):
        msg = "Missing language_code identifier"
        log_entry(severity="ERROR", message=msg, **entry)
        return msg, 422

    if not (region_code := data.get("region_code")):
        msg = "Missing region_code identifier"
        log_entry(severity="ERROR", message=msg, **entry)
        return msg, 422

    template_id = template_id_mapping.get(
        (form_type, region_code, language_code), os.getenv("NOTIFY_TEST_TEMPLATE_ID")
    )

    if not template_id:
        msg = "No template id selected"
        log_entry(severity="ERROR", message=msg, **entry)
        return msg, 422

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

    kwargs = json.dumps(
        {
            "template_id": template_id,
            "personalisation": {"address": data["display_address"]},
            "email_address": data["email_address"],
        }
    )

    try:
        response = session.post(
            f"{NOTIFY_BASE_URL}/notifications/email",
            kwargs,
        )
        response.raise_for_status()
        entry = dict(
            severity="INFO",
            message="notify email requested",
            tx_id=data.get("tx_id"),
            questionnaire_id=data.get("questionnaire_id"),
        )
        log_entry(**entry)
    except RequestException as error:
        error_message = error.response.json()["errors"][0]
        status_code = error.response.status_code
        entry = dict(
            severity="ERROR",
            status_code=status_code,
            message=f"notify request failed: {error_message}",
            tx_id=data.get("tx_id"),
            questionnaire_id=data.get("questionnaire_id"),
        )
        log_entry(**entry)
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
