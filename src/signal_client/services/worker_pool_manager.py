from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

import structlog
from dependency_injector import providers

from signal_client.command import Command, CommandError
from signal_client.context import Context
from signal_client.exceptions import UnsupportedMessageError
from signal_client.infrastructure.schemas.message import Message
from signal_client.metrics import (
    ERRORS_OCCURRED,
    MESSAGE_QUEUE_DEPTH,
    MESSAGE_QUEUE_LATENCY,
    MESSAGES_PROCESSED,
)
from signal_client.services.message_parser import MessageParser
from signal_client.services.models import QueuedMessage

log = structlog.get_logger()

MiddlewareCallable = Callable[
    [Context, Callable[[Context], Awaitable[None]]], Awaitable[None]
]


@dataclass(slots=True)
class WorkerConfig:
    context_factory: providers.Factory[Context]
    queue: asyncio.Queue[QueuedMessage]
    commands: dict[str, Command]
    message_parser: MessageParser
    sensitive_trigger_regex: re.Pattern[str] | None
    insensitive_trigger_regex: re.Pattern[str] | None
    sensitive_triggers: list[str]
    insensitive_triggers: list[str]
    regex_commands: list[tuple[re.Pattern[str], Command]]
    middleware: Iterable[MiddlewareCallable]


class Worker:
    def __init__(self, config: WorkerConfig, worker_id: int = 0) -> None:
        self._context_factory = config.context_factory
        self._queue = config.queue
        self._commands = config.commands
        self._message_parser = config.message_parser
        self._sensitive_trigger_regex = config.sensitive_trigger_regex
        self._insensitive_trigger_regex = config.insensitive_trigger_regex
        self._sensitive_triggers = config.sensitive_triggers
        self._insensitive_triggers = config.insensitive_triggers
        self._regex_commands = list(config.regex_commands)
        self._middleware: list[MiddlewareCallable] = list(config.middleware)
        self._stop = asyncio.Event()
        self._worker_id = worker_id

    def stop(self) -> None:
        """Stop the worker."""
        self._stop.set()

    async def process_messages(self) -> None:
        """Continuously process messages from the queue."""
        while not self._stop.is_set():
            try:
                queued_item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                if isinstance(queued_item, str):
                    queued_message = QueuedMessage(
                        raw=queued_item,
                        enqueued_at=time.perf_counter(),
                    )
                else:
                    queued_message = queued_item

                latency = time.perf_counter() - queued_message.enqueued_at
                try:
                    MESSAGE_QUEUE_LATENCY.observe(latency)
                    structlog.contextvars.bind_contextvars(
                        worker_id=self._worker_id,
                        queue_depth=self._queue.qsize(),
                    )
                    message = self._message_parser.parse(queued_message.raw)
                    if message:
                        await self.process(message, latency)
                        MESSAGES_PROCESSED.inc()
                except UnsupportedMessageError as e:
                    log.debug("Ignoring unsupported message", error=e)
                    ERRORS_OCCURRED.inc()
                except (json.JSONDecodeError, KeyError):
                    log.exception(
                        "worker.message_parse_failed",
                        raw_message=queued_message.raw,
                        worker_id=self._worker_id,
                    )
                    ERRORS_OCCURRED.inc()
                finally:
                    self._queue.task_done()
                    MESSAGE_QUEUE_DEPTH.set(self._queue.qsize())
                    structlog.contextvars.clear_contextvars()
            except asyncio.TimeoutError:  # noqa: PERF203
                continue

    async def process(
        self, message: Message, queue_latency: float | None = None
    ) -> None:
        """Process a single message."""
        structlog.contextvars.bind_contextvars(
            message_id=message.id,
            source=message.source,
            timestamp=message.timestamp,
        )
        context = self._context_factory(message=message)
        text = context.message.message
        if not isinstance(text, str) or not text:
            return

        command, trigger = self._select_command(text)
        if command is None or not self._is_whitelisted(command, context):
            return

        try:
            handler = getattr(command, "handle", None)
            handler_name = getattr(handler, "__name__", command.__class__.__name__)
            structlog.contextvars.bind_contextvars(
                command_name=handler_name,
                worker_id=self._worker_id,
                queue_latency=queue_latency,
            )
            await self._execute_with_middleware(command, context)
        except Exception:
            log.exception(
                "worker.command_failed",
                command_name=handler_name,
                trigger=trigger,
                worker_id=self._worker_id,
                queue_latency=queue_latency,
                message_id=str(message.id),
            )
            ERRORS_OCCURRED.inc()

    def _select_command(self, text: str) -> tuple[Command | None, str | None]:
        if self._insensitive_trigger_regex:
            match = self._insensitive_trigger_regex.match(text)
            if match and match.lastindex is not None:
                trigger = self._insensitive_triggers[match.lastindex - 1]
                return self._commands[trigger], trigger

        if self._sensitive_trigger_regex:
            match = self._sensitive_trigger_regex.match(text)
            if match and match.lastindex is not None:
                trigger = self._sensitive_triggers[match.lastindex - 1]
                return self._commands[trigger], trigger

        for pattern, regex_command in self._regex_commands:
            if pattern.search(text):
                return regex_command, pattern.pattern

        return None, None

    @staticmethod
    def _is_whitelisted(command: Command, context: Context) -> bool:
        if not command.whitelisted:
            return True
        return context.message.source in command.whitelisted

    async def _execute_with_middleware(
        self, command: Command, context: Context
    ) -> None:
        if command.handle is None:
            message = "Command handler is not configured."
            raise CommandError(message)

        async def invoke(index: int, ctx: Context) -> None:
            if index >= len(self._middleware):
                await command.handle(ctx)
                return

            middleware_fn = self._middleware[index]

            async def next_callable(next_ctx: Context) -> None:
                await invoke(index + 1, next_ctx)

            await middleware_fn(ctx, next_callable)

        await invoke(0, context)

    def add_middleware(self, middleware: MiddlewareCallable) -> None:
        self._middleware.append(middleware)


class WorkerPoolManager:
    def __init__(
        self,
        context_factory: providers.Factory[Context],
        queue: asyncio.Queue[QueuedMessage],
        message_parser: MessageParser,
        pool_size: int = 4,
    ) -> None:
        self._context_factory = context_factory
        self._queue = queue
        self._message_parser = message_parser
        self._pool_size = pool_size
        self._commands: dict[str, Command] = {}
        self._regex_commands: list[tuple[re.Pattern[str], Command]] = []
        self._registered_regex: set[tuple[int, str, int]] = set()
        self._workers: list[Worker] = []
        self._tasks: list[asyncio.Task] = []
        self._sensitive_triggers: list[str] = []
        self._insensitive_triggers: list[str] = []
        self._sensitive_trigger_regex: re.Pattern[str] | None = None
        self._insensitive_trigger_regex: re.Pattern[str] | None = None
        self._started = asyncio.Event()
        self._middleware: list[MiddlewareCallable] = []
        self._middleware_ids: set[int] = set()

    def register(self, command: Command) -> None:
        """Register a new command."""
        for trigger in command.triggers:
            if isinstance(trigger, str):
                if trigger in self._commands:
                    log.warning("Overwriting trigger", trigger=trigger)
                self._commands[trigger] = command
            elif isinstance(trigger, re.Pattern):
                key = (id(command), trigger.pattern, trigger.flags)
                if key in self._registered_regex:
                    continue
                self._regex_commands.append((trigger, command))
                self._registered_regex.add(key)

    def start(self) -> None:
        """Start the worker pool."""
        self._compile_triggers()
        for worker_id in range(self._pool_size):
            worker_config = WorkerConfig(
                context_factory=self._context_factory,
                queue=self._queue,
                commands=self._commands,
                message_parser=self._message_parser,
                sensitive_trigger_regex=self._sensitive_trigger_regex,
                insensitive_trigger_regex=self._insensitive_trigger_regex,
                sensitive_triggers=self._sensitive_triggers,
                insensitive_triggers=self._insensitive_triggers,
                regex_commands=self._regex_commands,
                middleware=self._middleware,
            )
            worker = Worker(worker_config, worker_id=worker_id)
            self._workers.append(worker)
            task = asyncio.create_task(worker.process_messages())
            self._tasks.append(task)
        self._started.set()

    def _compile_triggers(self) -> None:
        """Compile the triggers into a single regex."""
        sensitive_triggers: list[str] = []
        insensitive_triggers: list[str] = []

        for trigger, command in self._commands.items():
            if command.case_sensitive:
                sensitive_triggers.append(trigger)
            else:
                insensitive_triggers.append(trigger)

        self._sensitive_triggers = sorted(sensitive_triggers)
        self._insensitive_triggers = sorted(insensitive_triggers)

        if self._sensitive_triggers:
            patterns = [f"({re.escape(t)})" for t in self._sensitive_triggers]
            self._sensitive_trigger_regex = re.compile("|".join(patterns))
        else:
            self._sensitive_trigger_regex = None

        if self._insensitive_triggers:
            patterns = [f"({re.escape(t)})" for t in self._insensitive_triggers]
            self._insensitive_trigger_regex = re.compile(
                "|".join(patterns), re.IGNORECASE
            )
        else:
            self._insensitive_trigger_regex = None

    def stop(self) -> None:
        """Stop the worker pool."""
        for worker in self._workers:
            worker.stop()

    def register_middleware(self, middleware: MiddlewareCallable) -> None:
        if id(middleware) in self._middleware_ids:
            return
        self._middleware.append(middleware)
        self._middleware_ids.add(id(middleware))
        for worker in self._workers:
            worker.add_middleware(middleware)

    async def join(self) -> None:
        """Wait for all worker tasks to complete."""
        await asyncio.gather(*self._tasks)
