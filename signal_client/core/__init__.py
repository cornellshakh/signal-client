"""Core domain types and helpers."""

from .command import Command, CommandError, CommandMetadata, command
from .compatibility import check_supported_versions
from .config import Settings
from .exceptions import (
    AuthenticationError,
    GroupNotFoundError,
    InvalidRecipientError,
    RateLimitError,
    ServerError,
    SignalAPIError,
    UnsupportedMessageError,
)

__all__ = [
    "AuthenticationError",
    "Command",
    "CommandError",
    "CommandMetadata",
    "Context",
    "ContextDependencies",
    "GroupNotFoundError",
    "InvalidRecipientError",
    "RateLimitError",
    "ServerError",
    "Settings",
    "SignalAPIError",
    "UnsupportedMessageError",
    "check_supported_versions",
    "command",
]


def __getattr__(name):
    if name in {"Context", "ContextDependencies"}:
        from . import context as _context

        return getattr(_context, name)
    raise AttributeError(f"module 'signal_client.core' has no attribute {name}")
