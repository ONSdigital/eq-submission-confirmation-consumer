import pytest


@pytest.mark.usefixtures("notify_function_process")
class TestNotify:
    payload = {
        "payload": {
            "fulfilmentRequest": {
                "email_address": "simulate-delivered@notifications.service.gov.uk",
                "display_address": "My House, at the end of my street",
                "form_type": "H",
                "language_code": "en",
                "region_code": "GB-ENG",
            }
        }
    }

    def test_successful(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.status_code == 201
        assert res.text == "notify request successful"

    # The following should not return the `expected` json in the payload
    # as the temp failure and permanent failure email address are used
    # (see https://docs.notifications.service.gov.uk/rest-api.html#test)
    @pytest.mark.xfail
    def test_temporary_error(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.status_code != 200

    @pytest.mark.xfail
    def test_permanent_error(self, base_url, requests_session):
        res = requests_session.post(base_url, json=self.payload)
        assert res.status_code != 200
