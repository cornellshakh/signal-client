"""Public package surface for signal-client."""

from .app import Application, SignalClient
from .core import Command, CommandError, Context, Settings, command
from .exceptions import (
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
    "Application",
    "AuthenticationError",
    "Command",
    "CommandError",
    "ConfigurationError",
    "Context",
    "GroupNotFoundError",
    "InvalidRecipientError",
    "RateLimitError",
    "ServerError",
    "Settings",
    "SignalAPIError",
    "SignalClient",
    "UnsupportedMessageError",
    "command",
]
