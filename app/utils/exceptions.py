class ErrorResponse(Exception):
    """Custom API error that maps to the standard failure envelope."""

    def __init__(
        self, status: int, message: str, errors: list[str] | None = None
    ) -> None:
        self.status = status
        self.message = message
        self.errors = errors


class RateLimitErrorResponse(Exception):
    """Rate limit exceeded."""

    def __init__(
        self, status: int, message: str, errors: list[str] | None = None
    ) -> None:
        self.status = status
        self.message = message
        self.errors = errors
