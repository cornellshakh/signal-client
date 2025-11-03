from __future__ import annotations

import asyncio
import json
import re

import structlog
from dependency_injector import providers

from signal_client.command import Command
from signal_client.context import Context
from signal_client.infrastructure.schemas.message import Message
from signal_client.services.message_parser import MessageParser
from signal_client.services.message_service import UnsupportedMessageError

log = structlog.get_logger()


class Worker:
    def __init__(
        self,
        context_factory: providers.Factory[Context],
        queue: asyncio.Queue[str],
        trigger_regex: re.Pattern[str],
        commands: dict[str, Command],
        message_parser: MessageParser,
    ) -> None:
        self._context_factory = context_factory
        self._queue = queue
        self._trigger_regex = trigger_regex
        self._commands = commands
        self._message_parser = message_parser
        self._stop = asyncio.Event()

    def stop(self) -> None:
        """Stop the worker."""
        self._stop.set()

    async def process_messages(self) -> None:
        """Continuously process messages from the queue."""
        while not self._stop.is_set():
            try:
                raw_message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                try:
                    message = self._message_parser.parse(raw_message)
                    if message:
                        await self.process(message)
                except UnsupportedMessageError as e:
                    log.debug("Ignoring unsupported message", error=e)
                except (json.JSONDecodeError, KeyError):
                    log.exception("Failed to parse message", raw_message=raw_message)
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:  # noqa: PERF203
                continue

    async def process(self, message: Message) -> None:
        """Process a single message."""
        context = self._context_factory(message=message)
        if not context.message.message or not isinstance(context.message.message, str):
            return

        text = context.message.message
        match = self._trigger_regex.match(text)
        if match:
            trigger = match.lastgroup
            if trigger:
                command = self._commands[trigger]
                # Whitelist check
                if (
                    command.whitelisted
                    and context.message.source not in command.whitelisted
                ):
                    return

                try:
                    await command.handle(context)
                except Exception:
                    log.exception(
                        "Command handler raised an exception",
                        command=command,
                        message=message,
                    )


class WorkerPoolManager:
    def __init__(
        self,
        context_factory: providers.Factory[Context],
        queue: asyncio.Queue[str],
        message_parser: MessageParser,
        pool_size: int = 4,
    ) -> None:
        self._context_factory = context_factory
        self._queue = queue
        self._message_parser = message_parser
        self._pool_size = pool_size
        self._commands: dict[str, Command] = {}
        self._workers: list[Worker] = []
        self._tasks: list[asyncio.Task] = []
        self._trigger_regex: re.Pattern[str] | None = None

    def register(self, command: Command) -> None:
        """Register a new command."""
        for trigger in command.triggers:
            if isinstance(trigger, str):
                if trigger in self._commands:
                    log.warning("Overwriting trigger", trigger=trigger)
                self._commands[trigger] = command

    def start(self) -> None:
        """Start the worker pool."""
        self._compile_triggers()
        if self._trigger_regex is None:
            return
        for _ in range(self._pool_size):
            worker = Worker(
                context_factory=self._context_factory,
                queue=self._queue,
                trigger_regex=self._trigger_regex,
                commands=self._commands,
                message_parser=self._message_parser,
            )
            self._workers.append(worker)
            task = asyncio.create_task(worker.process_messages())
            self._tasks.append(task)

    def _compile_triggers(self) -> None:
        """Compile the triggers into a single regex."""
        if not self._commands:
            self._trigger_regex = re.compile("a^")  # A regex that will never match
            return
        trigger_patterns = []
        for trigger, command in self._commands.items():
            pattern = re.escape(trigger)
            if not command.case_sensitive:
                pattern = f"(?i){pattern}"
            trigger_patterns.append(f"(?P<{trigger}>{pattern})")
        self._trigger_regex = re.compile("|".join(trigger_patterns))

    def stop(self) -> None:
        """Stop the worker pool."""
        for worker in self._workers:
            worker.stop()

    async def join(self) -> None:
        """Wait for all worker tasks to complete."""
        await asyncio.gather(*self._tasks)
