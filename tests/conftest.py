import os
import signal
import subprocess
from os.path import dirname

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
        preexec_fn=os.setsid,
    )

    yield process

    # Stop the functions framework process
    print("\nTearing down functions-framework")
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


@pytest.fixture(scope="module")
def base_url():
    port = os.getenv("PORT", "8080")
    return f"http://localhost:{port}"


@pytest.fixture(scope="module")
def requests_session(base_url):
    retry_policy = Retry(total=6, backoff_factor=6)
    retry_adapter = requests.adapters.HTTPAdapter(max_retries=retry_policy)

    session = requests.Session()
    session.mount(base_url, retry_adapter)

    return session
