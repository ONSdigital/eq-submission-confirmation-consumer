import os
import random
import string
from unittest.mock import Mock
from uuid import uuid4

import pytest
import responses

from exceptions import InvalidNotifyKeyError
from main import NOTIFY_BASE_URL, create_notify_token, send_email

url = f"{NOTIFY_BASE_URL}/notifications/email"

success_json = {
    "id": "740e5834-3a29-46b4-9a6f-16142fde533a",
    "reference": "STRING",
    "content": {
        "subject": "SUBJECT TEXT",
        "body": "MESSAGE TEXT",
        "from_email": "SENDER EMAIL",
    },
    "uri": f"{NOTIFY_BASE_URL}/notifications/740e5834-3a29-46b4-9a6f-16142fde533a",
    "template": {
        "id": "f33517ff-2a88-4f6e-b855-c550268ce08a",
        "version": "6.0.1",
        "uri": f"{NOTIFY_BASE_URL}/template/f33517ff-2a88-4f6e-b855-c550268ce08a",
    },
}


def test_get_not_allowed():
    request = Mock(method="GET")
    response = send_email(request)
    assert response == ("Method not allowed", 405)


def test_missing_data_returns_422():
    request = Mock(method="POST", json={})
    response = send_email(request)
    assert response == ("Missing notification request data", 422)


def test_invalid_service_id_raises_invalid_notify_key_error():
    random_string = "".join(random.choice(string.printable) for i in range(87))
    with pytest.raises(InvalidNotifyKeyError):
        create_notify_token(random_string)


def test_invalid_api_key_raises_invalid_notify_key_error():
    random_string = "".join(random.choice(string.printable) for i in range(37))
    uuid_string = str(uuid4())
    with pytest.raises(InvalidNotifyKeyError):
        create_notify_token(uuid_string + random_string)


@responses.activate
def test_notify_response_error_returns_correctly():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "form_type": "HH",
                    "language_code": "en",
                    "region_code": "GB-ENG",
                }
            },
        },
    )
    responses.add(responses.POST, url, json={"errors": "403"}, status=403)
    response = send_email(request)
    assert response == ("Notify request failed", 403)


@responses.activate
def test_notify_response_no_content_204():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "form_type": "HH",
                    "language_code": "en",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
    responses.add(responses.POST, url, json={}, status=204)
    response = send_email(request)
    assert response == ("No content", 204)


@responses.activate
def test_notify_response_json_decode_error():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "form_type": "HH",
                    "language_code": "en",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
    responses.add(responses.POST, url, status=200)
    response = send_email(request)
    assert response == ("Notify JSON response object failed decoding", 503)


@responses.activate
def test_send_email():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "test": [],
                    "form_type": "HH",
                    "language_code": "en",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
    responses.add(responses.POST, url, json=success_json, status=200)
    response = send_email(request)
    assert response == success_json


@responses.activate
def test_missing_form_type():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "test": [],
                    "language_code": "en",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
    response = send_email(request)
    assert response == ("Missing form_type identifier(s)", 422)


@responses.activate
def test_missing_language_code():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "test": [],
                    "form_type": "HH",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
    response = send_email(request)
    assert response == ("Missing language_code identifier(s)", 422)


@responses.activate
def test_missing_region_code():
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "test": [],
                    "form_type": "HH",
                    "language_code": "en",
                },
            },
        },
    )
    response = send_email(request)
    assert response == ("Missing region_code identifier(s)", 422)


@responses.activate
def test_no_valid_template_selected():
    os.environ["NOTIFY_TEST_TEMPLATE_ID"] = ""
    request = Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "test@example.com",
                    "personalisation": {"address": "test address"},
                    "test": [],
                    "form_type": "not-a-form-type",
                    "language_code": "not-a-key",
                    "region_code": "not-a-region-code",
                },
            },
        },
    )

    response = send_email(request)
    assert response == ("No template id selected", 422)
