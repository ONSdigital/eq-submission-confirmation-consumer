import json
import os
from datetime import datetime, timezone
from typing import Mapping, NamedTuple, Tuple
from uuid import UUID

import google.auth
import jwt
from flask import Request
from google.cloud import secretmanager
from requests import Session
from requests.exceptions import RequestException

from exceptions import InvalidNotifyKeyError, InvalidRequestError

NOTIFY_BASE_URL = "https://api.notifications.service.gov.uk/v2"

if (notify_api_key := os.getenv("NOTIFY_API_KEY")) is None:
    _, project_id = google.auth.default()
    client = secretmanager.SecretManagerServiceClient()
    secret_manager_response = client.access_secret_version(
        name=f"projects/{project_id}/secrets/notify_api_key/versions/latest"
    )
    notify_api_key = secret_manager_response.payload.data.decode("UTF-8")


class NotifyRequestArgs(NamedTuple):
    template_id: str
    email_address: str
    address: str


def log_info(message, **kwargs):
    print(json.dumps({"message": message, "severity": "INFO", **kwargs}))


def log_error(message, **kwargs):
    print(json.dumps({"message": message, "severity": "ERROR", **kwargs}))


service_id = notify_api_key[-73:-37]
secret_key = notify_api_key[-36:]


def _is_valid_uuid(identifier: str) -> bool:
    try:
        UUID(identifier, version=4)
    except ValueError:
        return False

    return True


if not _is_valid_uuid(service_id):
    raise InvalidNotifyKeyError("Service ID is not a valid uuid")

if not _is_valid_uuid(secret_key):
    raise InvalidNotifyKeyError("API key is not a valid uuid")


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


def _parse_request(request: Request) -> Tuple[NotifyRequestArgs, Mapping]:
    if not request.method == "POST":
        raise InvalidRequestError("method not allowed", 405)

    if not request.json:
        raise InvalidRequestError("missing notification request data", 422)

    fulfilment_request = request.json["payload"]["fulfilmentRequest"]

    log_context = {
        "tx_id": fulfilment_request.get("tx_id"),
        "questionnaire_id": fulfilment_request.get("questionnaire_id"),
    }

    required_keys = (
        "form_type",
        "region_code",
        "language_code",
        "email_address",
        "display_address",
    )
    if missing_keys := [
        key for key in required_keys if not fulfilment_request.get(key)
    ]:
        msg = f"missing {', '.join(missing_keys)} identifier(s)"
        raise InvalidRequestError(msg, 422, log_context)

    try:
        template_id = template_id_mapping[
            (
                fulfilment_request["form_type"],
                fulfilment_request["region_code"],
                fulfilment_request["language_code"],
            )
        ]
    except KeyError as exc:
        raise InvalidRequestError("no template id selected", 422, log_context) from exc

    return (
        NotifyRequestArgs(
            template_id,
            fulfilment_request["email_address"],
            fulfilment_request["display_address"],
        ),
        log_context,
    )


def create_jwt_token(secret: str, client_id: str) -> str:
    headers = {"typ": "JWT", "alg": "HS256"}
    claims = {"iss": client_id, "iat": int(datetime.now(timezone.utc).timestamp())}
    return jwt.encode(payload=claims, key=secret, headers=headers)


# pylint: disable=too-many-return-statements
def send_email(request: Request) -> Tuple[str, int]:
    try:
        notify_request_args, log_context = _parse_request(request)
    except InvalidRequestError as error:
        log_context = error.log_context if error.log_context else {}
        log_error(error.message, **log_context)
        return error.message, error.status_code

    api_token = create_jwt_token(secret_key, service_id)
    session.headers.update(
        {
            "Content-type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }
    )

    post_args = json.dumps(
        {
            "template_id": notify_request_args.template_id,
            "personalisation": {"address": notify_request_args.address},
            "email_address": notify_request_args.email_address,
        }
    )

    try:
        response = session.post(
            f"{NOTIFY_BASE_URL}/notifications/email",
            post_args,
        )
        response.raise_for_status()
        log_info("notify email requested", **log_context)
    except RequestException as error:
        notify_error = error.response.json()["errors"][0]
        status_code = error.response.status_code
        message = "notify request failed"
        log_error(
            message,
            **log_context,
            notify_error=notify_error,
            status_code=status_code,
        )
        return message, error.response.status_code

    if response.status_code == 204:
        return "no content", 204

    try:
        notify_response = response.json()
        del notify_response["content"]
        message = "notify request successful"
        log_info(message, notify_response=notify_response, **log_context)
        return message, response.status_code
    except ValueError:
        message = "notify JSON response object failed decoding"
        log_error(message, **log_context)
        return message, 500
