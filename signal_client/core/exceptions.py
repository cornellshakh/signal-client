"""Custom exceptions for the Signal client."""

from __future__ import annotations


class SignalClientError(Exception):
    """Base exception for all signal-client errors."""


class SignalAPIError(Exception):
    """Base exception for all API-related errors.

    This exception is raised for general API errors that do not fall into
    more specific categories (e.g., unexpected status codes).
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Store an API error message and optional status code."""
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(SignalAPIError):
    """Raised when the API rate limit is exceeded (HTTP status codes 413 or 429)."""

    def __init__(self, message: str, status_code: int | None = 429) -> None:
        """Initialize a rate limit error."""
        super().__init__(message, status_code)


class InvalidRecipientError(SignalAPIError):
    """Raised when a message cannot be sent due to an invalid recipient.

    Applies to HTTP status 404 on send operations.
    """

    def __init__(self, message: str, status_code: int | None = 404) -> None:
        """Initialize an invalid recipient error."""
        super().__init__(message, status_code)


class GroupNotFoundError(SignalAPIError):
    """Raised when a requested group is not found (HTTP status 404.

    For group-related operations).
    """

    def __init__(self, message: str, status_code: int | None = 404) -> None:
        """Initialize a group-not-found error."""
        super().__init__(message, status_code)


class AuthenticationError(SignalAPIError):
    """Raised for authentication failures (HTTP status code 401 Unauthorized)."""

    def __init__(self, message: str, status_code: int | None = 401) -> None:
        """Initialize an authentication error."""
        super().__init__(message, status_code)


class ServerError(SignalAPIError):
    """Raised for server-side errors (HTTP status codes 5xx)."""

    def __init__(self, message: str, status_code: int | None = 500) -> None:
        """Initialize a server error."""
        super().__init__(message, status_code)


class UnsupportedMessageError(SignalClientError):
    """Custom exception for unsupported message types encountered during processing."""


class ConfigurationError(Exception):
    """Raised when there is an issue with the application's configuration."""
