from __future__ import annotations


class SignalClientError(Exception):
    """Base exception for all signal-client errors."""


class APIError(SignalClientError):
    """Raised when the Signal API returns an error."""


class AuthenticationError(APIError):
    """Raised for authentication errors (401)."""


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""


class ServerError(APIError):
    """Raised for server-side errors (5xx)."""
