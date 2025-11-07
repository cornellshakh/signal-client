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
    name: str | None = None
    description: str | None = None
    usage: str | None = None


class Command:
    def __init__(
        self,
        triggers: list[str | re.Pattern],
        whitelisted: list[str] | None = None,
        *,
        case_sensitive: bool = False,
        metadata: CommandMetadata | None = None,
    ) -> None:
        self.triggers = triggers
        self.whitelisted = whitelisted or []
        self.case_sensitive = case_sensitive
        meta = metadata or CommandMetadata()
        self.name = meta.name
        self.description = meta.description
        self.usage = meta.usage
        self.handle: Callable[[Context], Awaitable[None]] | None = None

    def with_handler(self, handler: Callable[[Context], Awaitable[None]]) -> Command:
        self.handle = handler
        if self.name is None:
            self.name = handler.__name__
        if self.description is None:
            doc = inspect.getdoc(handler)
            self.description = doc.strip() if doc else None
        return self

    async def __call__(self, context: Context) -> None:
        if self.handle is None:
            message = _COMMAND_HANDLER_NOT_SET
            raise CommandError(message)
        await self.handle(context)


class CommandError(Exception):
    pass


def command(
    *triggers: str | re.Pattern,
    whitelisted: Sequence[str] | None = None,
    case_sensitive: bool = False,
    name: str | None = None,
    description: str | None = None,
    usage: str | None = None,
) -> Callable[[Callable[[Context], Awaitable[None]]], Command]:
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
