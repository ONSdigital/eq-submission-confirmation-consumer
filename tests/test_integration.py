import os
from copy import copy

import pytest
import requests
from urllib3.util.retry import Retry

expected = {
    "content": {
        "body": "# Thanks for submitting the census\r\nYour census has been submitted for the household at My House, at the end of my street.\r\n\r\n^Your personal information is protected by law and will be kept confidential. \r\n\r\nIf you have any questions about the census, visit https://www.census.gov.uk\r\n\r\n---\r\n\r\nThe Office for National Statistics (ONS) is responsible for planning and running the census in England and Wales. You can find out more about ONS at https://www.ons.gov.uk/",
        "from_email": "census.2021@notifications.service.gov.uk",
        "subject": "Confirmation – your census has been submitted",
    },
    "id": "9e5020e2-35f5-4ee4-9ec9-789c7e433bfe",
    "reference": None,
    "scheduled_for": None,
    "template": {
        "id": "0c5a4f95-bfa4-4364-9394-8499b4d777d5",
        "uri": "https://api.notifications.service.gov.uk/services/0e515090-7962-40e8-a8c7-acbacf079c21/templates/0c5a4f95-bfa4-4364-9394-8499b4d777d5",
        "version": 1,
    },
    "uri": "https://api.notifications.service.gov.uk/v2/notifications/9e5020e2-35f5-4ee4-9ec9-789c7e433bfe",
}


@pytest.mark.usefixtures("notify_function_process")
class TestNotify:
    payload = {
        "email_address": "test@example.com",
        "display_address": "My House, at the end of my street",
        "form_type": "HH",
        "language_code": "en",
        "region_code": "Eng",
    }

    def test_successful(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.json()["content"] == expected["content"]

    # The following should not return the `expected` json in the payload
    # as the temp failure and permanent failure email address are used
    # (see https://docs.notifications.service.gov.uk/rest-api.html#test)
    @pytest.mark.xfail
    def test_temporary_error(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.json()["content"] != expected["content"]

    @pytest.mark.xfail
    def test_permanent_error(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.json()["content"] != expected["content"]

    def test_missing_address(self, base_url, requests_session):
        payload = copy(self.payload)
        del payload["display_address"]
        res = requests_session.post(base_url, json=payload)
        assert res.status_code == 400
        assert res.text == "Notify request failed"

    def test_missing_email(self, base_url, requests_session):
        payload = copy(self.payload)
        del payload["email_address"]
        res = requests_session.post(base_url, json=payload)
        assert res.status_code == 400
        assert res.text == "Notify request failed"
