from __future__ import annotations


class SignalClientError(Exception):
    """Base exception for all signal-client errors."""


class APIError(SignalClientError):
    """Raised when the Signal API returns an error."""

    def __init__(
        self,
        message: str = "API error",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.docs_url = docs_url
        if status_code:
            message = f"{message} (Status Code: {status_code})"
        if response_body:
            message = f"{message}\nResponse: {response_body}"
        if docs_url:
            message = f"{message}\n\nSee {docs_url} for more information."
        super().__init__(message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        message = super().__str__()
        if self.status_code:
            message = f"Status Code: {self.status_code}\n{message}"
        return message

    def to_dict(self) -> dict[str, str | int | None]:
        """Return a dictionary representation of the error."""
        return {
            "message": self.args[0],
            "status_code": self.status_code,
            "response_body": self.response_body,
            "docs_url": self.docs_url,
        }


class AuthenticationError(APIError):
    """Raised for authentication errors (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, docs_url)


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, docs_url)


class ConflictError(APIError):
    """Raised when there is a conflict (409)."""

    def __init__(
        self,
        message: str = "Conflict",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, docs_url)


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, docs_url)


class ServerError(APIError):
    """Raised for server-side errors (5xx)."""

    def __init__(
        self,
        message: str = "Server error",
        status_code: int | None = None,
        response_body: str | None = None,
        docs_url: str | None = None,
    ) -> None:
        super().__init__(message, status_code, response_body, docs_url)


class UnsupportedMessageError(SignalClientError):
    """Custom exception for unsupported message types."""
