import os
import signal
import subprocess
from os.path import dirname
from unittest.mock import Mock

import pytest
import requests
from urllib3.util.retry import Retry


@pytest.fixture(scope="session")
def notify_function_process():
    cwd = dirname(dirname(__file__))

    process = subprocess.Popen(
        ["pipenv run functions-framework --target=send_email --debug"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        shell=True,
        start_new_session=True,
    )

    yield process

    # Stop the functions framework process
    print("\nTearing down functions-framework")
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


@pytest.fixture(scope="module")
def base_url():
    port = os.getenv("PORT", "8080")
    return f"http://localhost:{port}"


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def requests_session(base_url):
    retry_policy = Retry(total=6, backoff_factor=6)
    retry_adapter = requests.adapters.HTTPAdapter(max_retries=retry_policy)

    session = requests.Session()
    session.mount(base_url, retry_adapter)

    return session


@pytest.fixture()
def mock_request():
    return Mock(
        method="POST",
        json={
            "payload": {
                "fulfilmentRequest": {
                    "email_address": "simulate-delivered@notifications.service.gov.uk",
                    "display_address": "test address",
                    "form_type": "H",
                    "language_code": "en",
                    "region_code": "GB-ENG",
                },
            },
        },
    )
