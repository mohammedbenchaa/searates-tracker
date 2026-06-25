"""
Exceptions used by SeaRates Tracker.
"""


class SeaRatesException(Exception):
    """Base exception for SeaRates Tracker errors."""

    def __init__(self, message: str, status: str = "error", raw_response: dict | None = None):
        self.message = message
        self.status = status
        self.raw_response = raw_response or {}
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.status}] {self.message}"


class SeaRatesAuthError(SeaRatesException):
    """Raised when authentication fails (missing or invalid API key)."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message=message, **kwargs)


class SeaRatesRateLimitError(SeaRatesException):
    """Raised when API rate limit is reached."""

    def __init__(self, message: str = "API rate limit reached", **kwargs):
        super().__init__(message=message, **kwargs)


class SeaRatesNotFoundError(SeaRatesException):
    """Raised when a tracking number is not found."""

    def __init__(self, message: str = "Tracking number not found", **kwargs):
        super().__init__(message=message, **kwargs)


class SeaRatesServerError(SeaRatesException):
    """Raised when the SeaRates server returns a 5xx error."""

    def __init__(self, message: str = "SeaRates server error", **kwargs):
        super().__init__(message=message, **kwargs)
