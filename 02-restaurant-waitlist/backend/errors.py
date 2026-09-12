class ServiceError(Exception):
    """Raised by services on business-rule violations; mapped to the API's Error schema."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
