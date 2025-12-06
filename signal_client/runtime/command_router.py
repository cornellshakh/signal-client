from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import structlog

from signal_client.core.command import Command

log = structlog.get_logger()


@dataclass(slots=True)
class _LiteralRegistration:
    trigger: str
    command: Command
    case_sensitive: bool
    trigger_lower: str


class CommandRouter:
    """Deterministic command matcher that preserves registration order."""

    def __init__(self) -> None:
        self._literal_triggers: list[_LiteralRegistration] = []
        self._regex_commands: list[tuple[re.Pattern[str], Command]] = []
        self._registered_regex: set[tuple[int, str, int]] = set()

    @property
    def regex_commands(self) -> Iterable[tuple[re.Pattern[str], Command]]:
        return tuple(self._regex_commands)

    @property
    def literal_triggers(self) -> Iterable[_LiteralRegistration]:
        return tuple(self._literal_triggers)

    def register(self, command: Command) -> None:
        for trigger in command.triggers:
            if isinstance(trigger, str):
                self._register_literal(
                    trigger, command, case_sensitive=command.case_sensitive
                )
            elif isinstance(trigger, re.Pattern):
                self._register_regex(trigger, command)

    def match(self, text: str) -> tuple[Command | None, str | None]:
        """Return the first matching command based on registration order."""
        for registration in self._literal_triggers:
            if registration.case_sensitive:
                if text.startswith(registration.trigger):
                    return registration.command, registration.trigger
            elif text.lower().startswith(registration.trigger_lower):
                return registration.command, registration.trigger

        for pattern, command in self._regex_commands:
            if pattern.search(text):
                return command, pattern.pattern

        return None, None

    def _register_literal(
        self, trigger: str, command: Command, *, case_sensitive: bool
    ) -> None:
        for registration in self._literal_triggers:
            if registration.trigger == trigger and registration.command is command:
                return
            if registration.trigger == trigger and registration.command is not command:
                log.warning(
                    "command_router.duplicate_literal_trigger",
                    trigger=trigger,
                    existing_command=id(registration.command),
                    new_command=id(command),
                )

        self._literal_triggers.append(
            _LiteralRegistration(
                trigger=trigger,
                command=command,
                case_sensitive=case_sensitive,
                trigger_lower=trigger.lower(),
            )
        )

    def _register_regex(self, pattern: re.Pattern[str], command: Command) -> None:
        key = (id(command), pattern.pattern, pattern.flags)
        if key in self._registered_regex:
            return
        self._regex_commands.append((pattern, command))
        self._registered_regex.add(key)


__all__ = ["CommandRouter"]
