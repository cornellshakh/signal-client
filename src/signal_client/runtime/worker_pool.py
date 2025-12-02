from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

import structlog

from signal_client.command import Command, CommandError
from signal_client.context import Context
from signal_client.exceptions import UnsupportedMessageError
from signal_client.infrastructure.schemas.message import Message
from signal_client.observability.metrics import (
    ERRORS_OCCURRED,
    MESSAGE_QUEUE_DEPTH,
    MESSAGE_QUEUE_LATENCY,
    MESSAGES_PROCESSED,
)
from signal_client.runtime.command_router import CommandRouter
from signal_client.runtime.models import QueuedMessage
from signal_client.services.message_parser import MessageParser

log = structlog.get_logger()

MiddlewareCallable = Callable[
    [Context, Callable[[Context], Awaitable[None]]], Awaitable[None]
]


@dataclass(slots=True)
class WorkerConfig:
    context_factory: Callable[[Message], Context]
    queue: asyncio.Queue[QueuedMessage]
    message_parser: MessageParser
    router: CommandRouter
    middleware: Iterable[MiddlewareCallable]


class Worker:
    def __init__(self, config: WorkerConfig, worker_id: int = 0) -> None:
        self._context_factory = config.context_factory
        self._queue = config.queue
        self._message_parser = config.message_parser
        self._router = config.router
        self._middleware: list[MiddlewareCallable] = list(config.middleware)
        self._stop = asyncio.Event()
        self._worker_id = worker_id

    def stop(self) -> None:
        self._stop.set()

    def add_middleware(self, middleware: MiddlewareCallable) -> None:
        self._middleware.append(middleware)

    async def process_messages(self) -> None:
        while not self._stop.is_set():
            try:
                queued_item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                queued_message = (
                    queued_item
                    if isinstance(queued_item, QueuedMessage)
                    else QueuedMessage(
                        raw=str(queued_item),
                        enqueued_at=time.perf_counter(),
                    )
                )
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
                except UnsupportedMessageError as error:
                    log.debug("worker.unsupported_message", error=error)
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

    async def process(  # compatibility alias for legacy tests/callers
        self, message: Message, queue_latency: float | None = None
    ) -> None:
        structlog.contextvars.bind_contextvars(
            message_id=message.id,
            source=message.source,
            timestamp=message.timestamp,
        )
        context = self._context_factory(message)
        text = context.message.message
        if not isinstance(text, str) or not text:
            return

        command, trigger = self._router.match(text)
        if command is None or not self._is_whitelisted(command, context):
            return

        handler = getattr(command, "handle", None)
        handler_name = getattr(handler, "__name__", command.__class__.__name__)
        try:
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


class WorkerPool:
    def __init__(
        self,
        context_factory: Callable[[Message], Context],
        queue: asyncio.Queue[QueuedMessage],
        message_parser: MessageParser,
        *,
        router: CommandRouter | None = None,
        pool_size: int = 4,
    ) -> None:
        self._context_factory = context_factory
        self._queue = queue
        self._message_parser = message_parser
        self._router = router or CommandRouter()
        self._pool_size = pool_size
        self._middleware: list[MiddlewareCallable] = []
        self._middleware_ids: set[int] = set()
        self._workers: list[Worker] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._started = asyncio.Event()

    @property
    def router(self) -> CommandRouter:
        return self._router

    def register(self, command: Command) -> None:
        self._router.register(command)

    def register_middleware(self, middleware: MiddlewareCallable) -> None:
        if id(middleware) in self._middleware_ids:
            return
        self._middleware.append(middleware)
        self._middleware_ids.add(id(middleware))
        for worker in self._workers:
            worker.add_middleware(middleware)

    def start(self) -> None:
        if self._started.is_set():
            return
        for worker_id in range(self._pool_size):
            worker_config = WorkerConfig(
                context_factory=self._context_factory,
                queue=self._queue,
                message_parser=self._message_parser,
                router=self._router,
                middleware=self._middleware,
            )
            worker = Worker(worker_config, worker_id=worker_id)
            self._workers.append(worker)
            task = asyncio.create_task(worker.process_messages())
            self._tasks.append(task)
        self._started.set()

    def stop(self) -> None:
        for worker in self._workers:
            worker.stop()

    async def join(self) -> None:
        if not self._tasks:
            return
        await asyncio.gather(*self._tasks)


__all__ = [
    "CommandRouter",
    "MiddlewareCallable",
    "Worker",
    "WorkerConfig",
    "WorkerPool",
]
