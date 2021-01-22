import os
import random
import string
from importlib import reload
from unittest import mock
from unittest.mock import Mock
from uuid import uuid4

import pytest
import responses

import main
from exceptions import InvalidNotifyKeyError
from main import NOTIFY_BASE_URL, send_email

url = f"{NOTIFY_BASE_URL}/notifications/email"


def test_get_not_allowed():
    request = Mock(method="GET")
    response = send_email(request)
    assert response == ("method not allowed", 405)


def test_missing_data_returns_422():
    request = Mock(method="POST", json={})
    response = send_email(request)
    assert response == ("missing notification request data", 422)


def test_invalid_service_id_raises_invalid_notify_key_error():
    random_string = "".join(random.choice(string.printable) for i in range(87))
    with mock.patch.dict(os.environ, {"NOTIFY_API_KEY": random_string}):
        with pytest.raises(InvalidNotifyKeyError):
            reload(main)


def test_invalid_api_key_raises_invalid_notify_key_error():
    random_string = "".join(random.choice(string.printable) for i in range(37))
    uuid_string = str(uuid4())
    with mock.patch.dict(os.environ, {"NOTIFY_API_KEY": uuid_string + random_string}):
        with pytest.raises(InvalidNotifyKeyError):
            reload(main)


@responses.activate
def test_notify_response_error_returns_correctly(mock_request):
    responses.add(responses.POST, url, json={"errors": "403"}, status=403)
    response = send_email(mock_request)
    assert response == ("notify request failed", 403)


@responses.activate
def test_notify_response_no_content_204(mock_request):
    responses.add(responses.POST, url, json={}, status=204)
    response = send_email(mock_request)
    assert response == ("no content", 204)


@responses.activate
def test_notify_response_json_decode_error(mock_request):
    # This shouldn't ever happen as it isn't a valid Notify response
    responses.add(responses.POST, url, status=200)
    response = send_email(mock_request)
    assert response == ("notify JSON response object failed decoding", 500)


@responses.activate
def test_send_email(mock_request):
    responses.add(responses.POST, url, json={"content": "ok"}, status=200)
    response = send_email(mock_request)
    assert response == ("notify request successful", 200)


@responses.activate
def test_missing_form_type(mock_request):
    del mock_request.json["payload"]["fulfilmentRequest"]["form_type"]
    response = send_email(mock_request)
    assert response == ("missing form_type identifier(s)", 422)


@responses.activate
def test_missing_language_code(mock_request):
    del mock_request.json["payload"]["fulfilmentRequest"]["language_code"]
    response = send_email(mock_request)
    assert response == ("missing language_code identifier(s)", 422)


@responses.activate
def test_missing_region_code(mock_request):
    del mock_request.json["payload"]["fulfilmentRequest"]["region_code"]
    response = send_email(mock_request)
    assert response == ("missing region_code identifier(s)", 422)


@responses.activate
def test_no_valid_template_selected(mock_request):
    mock_request.json["payload"]["fulfilmentRequest"]["form_type"] = "not-valid"
    response = send_email(mock_request)
    assert response == ("no template id selected", 422)
