from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import re

    from .context import Context


class Command(Protocol):
    triggers: list[str | re.Pattern]
    whitelisted: list[str]
    case_sensitive: bool

    async def handle(self, context: Context) -> None: ...


class CommandError(Exception):
    pass
