class InvalidNotifyKeyError(Exception):
    """Raised when Gov Notify key is malformed."""


class InvalidRequestError(Exception):
    """Raised when an invalid HTTP request is validated."""

    def __init__(self, message=None, status_code=None, log_context=None):
        self.message = message
        self.status_code = status_code
        self.log_context = log_context
        super().__init__()
