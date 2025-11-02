from __future__ import annotations


class SignalClientError(Exception):
    """Base exception for all signal-client errors."""


class APIError(SignalClientError):
    """Raised when the Signal API returns an error."""

    def __init__(self, message: str = "API error") -> None:
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised for authentication errors (401)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class ServerError(APIError):
    """Raised for server-side errors (5xx)."""

    def __init__(self, message: str = "Server error") -> None:
        super().__init__(message)


class UnsupportedMessageError(SignalClientError):
    """Custom exception for unsupported message types."""
