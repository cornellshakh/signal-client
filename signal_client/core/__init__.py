"""Core domain types and helpers."""

from .command import Command, CommandError, CommandMetadata, command
from .compatibility import check_supported_versions
from .config import Settings
from .context import Context
from .context_deps import ContextDependencies
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
