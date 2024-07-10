import pytest


@pytest.mark.usefixtures("notify_function_process")
class TestNotify:
    payload_template = {
        "payload": {
            "fulfilmentRequest": {
                "email_address": "",
                "display_address": "My House, at the end of my street",
                "form_type": "H",
                "language_code": "en",
                "region_code": "GB-ENG",
            }
        }
    }

    def set_email(self, email):
        payload_copy = self.payload_template.copy()
        payload_copy["payload"]["fulfilmentRequest"]["email_address"] = email
        return payload_copy

    # The following tests will not work as the Notify API key has been removed
    # until a mock service can be introduced
    # (see https://github.com/ONSdigital/eq-submission-confirmation-consumer/pull/12)
    def test_successful(self, base_url, requests_session):
        payload = self.set_email("simulate-delivered-2@notifications.service.gov.uk")
        res = requests_session.post(base_url, json=payload)
        assert res.status_code == 201
        assert res.text == "notify request successful"

    @pytest.mark.xfail
    def test_temporary_error(self, base_url, requests_session):
        """
        This test should return a 201 because the email only fails temporary
        """
        payload = self.set_email("temp-fail@simulator.notify")
        res = requests_session.post(base_url, json=payload)
        assert res.status_code == 201
        assert res.text == "notify request successful"

    @pytest.mark.xfail
    def test_permanent_error(self, base_url, requests_session):
        """
        The following should not return the `expected` json in the payload
        as the permanent failure email address are used
        (see https://docs.notifications.service.gov.uk/rest-api.html#test)
        """
        payload = self.set_email("perm-fail@simulator.notify")
        res = requests_session.post(base_url, json=payload)
        assert res.status_code != 200
