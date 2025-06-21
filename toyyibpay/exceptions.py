"""Custom exceptions for ToyyibPay SDK."""

from typing import Optional, Dict, Any


class ToyyibPayError(Exception):
    """Base exception for ToyyibPay SDK."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.response = response


class ConfigurationError(ToyyibPayError):
    """Raised when there's a configuration error."""
    pass


class AuthenticationError(ToyyibPayError):
    """Raised when authentication fails."""
    pass


class APIError(ToyyibPayError):
    """Raised when API returns an error."""
    pass


class ValidationError(ToyyibPayError):
    """Raised when validation fails."""
    pass


class NetworkError(ToyyibPayError):
    """Raised when network request fails."""
    pass


class TimeoutError(ToyyibPayError):
    """Raised when request times out."""
    pass


class RateLimitError(ToyyibPayError):
    """Raised when rate limit is exceeded."""
    pass


class InvalidRequestError(ToyyibPayError):
    """Raised when request is invalid."""
    pass


class PaymentError(ToyyibPayError):
    """Raised when payment processing fails."""
    pass


class WebhookError(ToyyibPayError):
    """Raised when webhook processing fails."""
    pass


class SignatureVerificationError(WebhookError):
    """Raised when webhook signature verification fails."""
    pass


class DatabaseError(ToyyibPayError):
    """Raised when database operation fails."""
    pass
