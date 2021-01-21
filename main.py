import json
import os
from datetime import datetime, timezone
from typing import Mapping, Tuple
from uuid import UUID

import jwt
from flask import Request
from requests import Session
from requests.exceptions import RequestException

from exceptions import InvalidNotifyKeyError, InvalidRequestError


def log_info(**kwargs):
    print(json.dumps({**kwargs, "severity": "INFO"}))


def log_error(**kwargs):
    print(json.dumps({**kwargs, "severity": "ERROR"}))


def _create_jwt_token(secret: str, client_id: str) -> str:
    headers = {"typ": "JWT", "alg": "HS256"}
    claims = {"iss": client_id, "iat": int(datetime.now(timezone.utc).timestamp())}
    return jwt.encode(payload=claims, key=secret, headers=headers)


def create_notify_token(key: str) -> str:
    service_id = key[-73:-37]
    secret_key = key[-36:]

    if not _is_valid_uuid(service_id):
        raise InvalidNotifyKeyError("Service ID is not a valid uuid")

    if not _is_valid_uuid(secret_key):
        raise InvalidNotifyKeyError("API key is not a valid uuid")

    return _create_jwt_token(secret_key, service_id)


def _is_valid_uuid(identifier: str) -> bool:
    try:
        UUID(identifier, version=4)
    except ValueError:
        return False

    return True


NOTIFY_API_KEY = os.environ["NOTIFY_API_KEY"]

NOTIFY_BASE_URL = "https://api.notifications.service.gov.uk/v2"

template_id_mapping = {
    ("H", "GB-ENG", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("H", "GB-WLS", "en"): "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
    ("H", "GB-WLS", "cy"): "755d73d1-0cb6-4f2f-95e9-857a2ad071bb",
    ("H", "GB-NIR", "en"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("H", "GB-NIR", "ga"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("H", "GB-NIR", "eo"): "0889cfa1-c0eb-4ba6-93d9-acc41b060152",
    ("I", "GB-ENG", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("I", "GB-WLS", "en"): "71de56dc-f83b-4899-93ab-7fe61e417c2e",
    ("I", "GB-WLS", "cy"): "1001ac43-093d-425c-ac7d-68df5147c603",
    ("I", "GB-NIR", "en"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("I", "GB-NIR", "ga"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("I", "GB-NIR", "eo"): "ed1c2e9f-c81e-4cc2-889c-8e0fa1d2ce1b",
    ("C", "GB-ENG", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("C", "GB-WLS", "en"): "4077d2cf-81cd-462d-9065-f227a7c39a8d",
    ("C", "GB-WLS", "cy"): "e4a4ebea-fcc8-463b-8686-5b8a7320f089",
}

data_fields = ("email_address", "display_address", "tx_id", "questionnaire_id")


session = Session()


def _validate_request(request: Request) -> Tuple[Mapping, str, Mapping]:
    if not request.method == "POST":
        # Note that Cloud Functions expect serialized JSON
        # to correctly log
        # https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
        raise InvalidRequestError("Method not allowed", 405)

    if not request.json:
        raise InvalidRequestError("Missing notification request data", 422)

    data = request.json["payload"]["fulfilmentRequest"]

    log_context = {
        "tx_id": data.get("tx_id"),
        "questionnaire_id": data.get("questionnaire_id"),
    }

    required_keys = ("form_type", "region_code", "language_code")
    if missing_keys := [key for key in required_keys if not data.get(key)]:
        msg = f"Missing {', '.join(missing_keys)} identifier(s)"
        raise InvalidRequestError(msg, 422, log_context)

    if not (
        template_id := template_id_mapping.get(
            (data["form_type"], data["region_code"], data["language_code"])
        )
    ):
        raise InvalidRequestError("No template id selected", 422, log_context)

    return {key: data.get(key) for key in data_fields}, template_id, log_context


# pylint: disable=too-many-return-statements
def send_email(request: Request) -> Tuple[str, int]:
    try:
        data, template_id, log_context = _validate_request(request)
    except InvalidRequestError as error:
        log_context = error.log_context if error.log_context else {}
        log_error(message=error.message, **log_context)
        return error.message, error.status_code

    api_token = create_notify_token(NOTIFY_API_KEY)
    session.headers.update(
        {
            "Content-type": "application/json",
            "Authorization": f"Bearer {api_token}",
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
        entry = dict(**log_context, message="notify email requested")
        log_info(**entry)
    except RequestException as error:
        error_message = error.response.json()["errors"][0]
        status_code = error.response.status_code
        log_error(
            **log_context,
            status_code=status_code,
            message=f"notify request failed: {error_message}",
        )
        return "Notify request failed", error.response.status_code

    if response.status_code == 204:
        return "No content", 204

    try:
        response_content = response.json()
        del response_content["content"]
        log_info(**log_context, **response_content)
        return "Notify request successful", response.status_code
    except ValueError:
        message = "Notify JSON response object failed decoding"
        log_error(**log_context, message=message)
        return message, 503
