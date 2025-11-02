from __future__ import annotations

import asyncio

from signal_client.command import Command
from signal_client.context import Context
from signal_client.domain.message import Message
from signal_client.infrastructure.api_service import APIService


class CommandService:
    def __init__(
        self,
        queue: asyncio.Queue[Message],
        api_service: APIService,
        phone_number: str,
    ) -> None:
        self._queue = queue
        self._api_service = api_service
        self._phone_number = phone_number
        self._commands: list[Command] = []

    def register(self, command: Command) -> None:
        """Register a new command."""
        self._commands.append(command)

    def get_commands(self) -> list[Command]:
        """Return the list of registered commands."""
        return self._commands

    async def process(self, message: Message) -> None:
        """Process a single message."""
        context = Context(message, self._api_service, self._phone_number)
        for command in self._commands:
            if self.should_trigger(command, context):
                await command.handle(context)

    async def process_messages(self) -> None:
        """Continuously process messages from the queue."""
        while True:
            message = await self._queue.get()
            try:
                await self.process(message)
            finally:
                self._queue.task_done()

    def should_trigger(self, command: Command, context: Context) -> bool:
        """Determine if a command should be triggered by a message."""
        if not context.message.message or not isinstance(context.message.message, str):
            return False

        # Whitelist check
        if command.whitelisted and context.message.source not in command.whitelisted:
            return False

        # Trigger check
        text = context.message.message
        if not command.case_sensitive:
            text = text.lower()

        for trigger in command.triggers:
            if isinstance(trigger, str):
                if text.startswith(trigger):
                    return True
            elif hasattr(trigger, "search") and trigger.search(text):
                return True

        return False
