"""Command definitions and decorator utilities for the Signal client."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import re

    from .context import Context

_COMMAND_HANDLER_NOT_SET = "Command handler has not been set."


@dataclass(slots=True)
class CommandMetadata:
    """Metadata associated with a command.

    Attributes:
        name: The name of the command (e.g., "echo").
        description: A brief description of what the command does.
        usage: Instructions on how to use the command.

    """

    name: str | None = None
    description: str | None = None
    usage: str | None = None


class Command:
    """Represents a single command that the bot can respond to.

    A command is defined by its triggers (patterns that match incoming messages),
    an optional whitelist of allowed senders, and a handler function that
    executes the command's logic.
    """

    def __init__(
        self,
        triggers: list[str | re.Pattern],
        whitelisted: list[str] | None = None,
        *,
        case_sensitive: bool = False,
        metadata: CommandMetadata | None = None,
    ) -> None:
        """Initialize a Command instance.

        Args:
            triggers: A list of strings or regular expressions that will
                      trigger this command.
            whitelisted: An optional list of sender IDs (phone numbers or group IDs)
                         that are allowed to execute this command. If empty or None,
                         all senders are allowed.
            case_sensitive: If True, string triggers will be matched case-sensitively.
                            Defaults to False.
            metadata: Optional CommandMetadata to provide name, description, and usage.

        """
        self.triggers = triggers
        self.whitelisted = whitelisted or []
        self.case_sensitive = case_sensitive
        meta = metadata or CommandMetadata()
        self.name = meta.name
        self.description = meta.description
        self.usage = meta.usage
        self.handle: Callable[[Context], Awaitable[None]] | None = None

    def with_handler(self, handler: Callable[[Context], Awaitable[None]]) -> Command:
        """Assign a handler function to this command.

        If name or description are not already set, they will be inferred
        from the handler function's name and docstring.

        Args:
            handler: The asynchronous function that will be executed when
                     this command is triggered. It must accept a Context object.

        Returns:
            The Command instance with the handler assigned.

        """
        self.handle = handler
        if self.name is None:
            self.name = handler.__name__
        if self.description is None:
            doc = inspect.getdoc(handler)
            self.description = doc.strip() if doc else None
        return self

    async def __call__(self, context: Context) -> None:
        """Execute the command's handler function.

        Args:
            context: The Context object containing message details and API clients.

        Raises:
            CommandError: If no handler has been assigned to the command.

        """
        if self.handle is None:
            message = _COMMAND_HANDLER_NOT_SET
            raise CommandError(message)
        await self.handle(context)


class CommandError(Exception):
    """Exception raised for errors specific to command execution."""


def command(
    *triggers: str | re.Pattern,
    whitelisted: Sequence[str] | None = None,
    case_sensitive: bool = False,
    name: str | None = None,
    description: str | None = None,
    usage: str | None = None,
) -> Callable[[Callable[[Context], Awaitable[None]]], Command]:
    """Define a new command via decorator.

    This decorator simplifies the creation of Command instances by allowing
    you to define triggers, whitelisted senders, and other metadata directly
    on the handler function.

    Args:
        *triggers: One or more strings or regular expressions that will
                   trigger this command.
        whitelisted: An optional list of sender IDs that are allowed to
                     execute this command.
        case_sensitive: If True, string triggers will be matched case-sensitively.
        name: An optional name for the command.
        description: An optional description for the command.
        usage: Optional usage instructions for the command.

    Returns:
        A decorator that transforms an asynchronous function into a Command object.

    Raises:
        ValueError: If no triggers are provided.

    """
    if not triggers:
        message = "At least one trigger must be provided."
        raise ValueError(message)

    metadata = CommandMetadata(name=name, description=description, usage=usage)

    def decorator(handler: Callable[[Context], Awaitable[None]]) -> Command:
        cmd = Command(
            triggers=list(triggers),
            whitelisted=list(whitelisted) if whitelisted is not None else None,
            case_sensitive=case_sensitive,
            metadata=metadata,
        )
        return cmd.with_handler(handler)

    return decorator
