from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import structlog

from signal_client.command import Command
from signal_client.context import Context
from signal_client.infrastructure.schemas.message import Message
from signal_client.services.message_parser import MessageParser
from signal_client.services.message_service import UnsupportedMessageError

if TYPE_CHECKING:
    from signal_client.container import Container


log = structlog.get_logger()


class Worker:
    def __init__(
        self,
        container: Container,
        queue: asyncio.Queue[str],
        commands: list[Command],
        message_parser: MessageParser,
    ) -> None:
        self._container = container
        self._queue = queue
        self._commands = commands
        self._message_parser = message_parser
        self._stop = asyncio.Event()

    def stop(self) -> None:
        """Stop the worker."""
        self._stop.set()

    async def process_messages(self) -> None:
        """Continuously process messages from the queue."""
        while not self._stop.is_set():
            get_task = asyncio.create_task(self._queue.get())
            stop_task = asyncio.create_task(self._stop.wait())

            done, _ = await asyncio.wait(
                {get_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
            )

            if get_task in done:
                raw_message = get_task.result()
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
                    stop_task.cancel()
            else:
                get_task.cancel()
                break

    async def process(self, message: Message) -> None:
        """Process a single message."""
        context = Context(container=self._container, message=message)
        for command in self._commands:
            if self.should_trigger(command, context):
                await command.handle(context)

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


class WorkerPoolManager:
    def __init__(
        self,
        queue: asyncio.Queue[str],
        message_parser: MessageParser,
        pool_size: int = 4,
    ) -> None:
        self._queue = queue
        self._message_parser = message_parser
        self._pool_size = pool_size
        self._commands: list[Command] = []
        self._workers: list[Worker] = []
        self._tasks: list[asyncio.Task] = []

    def register(self, command: Command) -> None:
        """Register a new command."""
        self._commands.append(command)

    def start(self, container: Container) -> None:
        """Start the worker pool."""
        for _ in range(self._pool_size):
            worker = Worker(
                container=container,
                queue=self._queue,
                commands=self._commands,
                message_parser=self._message_parser,
            )
            self._workers.append(worker)
            task = asyncio.create_task(worker.process_messages())
            self._tasks.append(task)

    def stop(self) -> None:
        """Stop the worker pool."""
        for worker in self._workers:
            worker.stop()

    async def join(self) -> None:
        """Wait for all worker tasks to complete."""
        await asyncio.gather(*self._tasks)
