"""Compatibility shim for public exceptions."""

from __future__ import annotations

from .core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    GroupNotFoundError,
    InvalidRecipientError,
    RateLimitError,
    ServerError,
    SignalAPIError,
    UnsupportedMessageError,
)

__all__ = [
    "AuthenticationError",
    "ConfigurationError",
    "GroupNotFoundError",
    "InvalidRecipientError",
    "RateLimitError",
    "ServerError",
    "SignalAPIError",
    "UnsupportedMessageError",
]
