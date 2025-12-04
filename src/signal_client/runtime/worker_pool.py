from __future__ import annotations

import asyncio
import json
import math
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
import logging
from zlib import crc32

import structlog

from signal_client.command import Command, CommandError
from signal_client.context import Context
from signal_client.exceptions import (
    AuthenticationError,
    GroupNotFoundError,
    InvalidRecipientError,
    RateLimitError,
    ServerError,
    SignalAPIError,
    UnsupportedMessageError,
)
from signal_client.infrastructure.schemas.message import Message
from signal_client.observability.metrics import (
    COMMAND_LATENCY,
    COMMANDS_PROCESSED,
    ERRORS_OCCURRED,
    MESSAGE_QUEUE_DEPTH,
    MESSAGE_QUEUE_LATENCY,
    MESSAGES_PROCESSED,
    SHARD_QUEUE_DEPTH,
)
from signal_client.runtime.command_router import CommandRouter
from signal_client.runtime.models import QueuedMessage
from signal_client.services.checkpoint_store import IngestCheckpointStore
from signal_client.services.dead_letter_queue import DeadLetterQueue
from signal_client.services.lock_manager import LockManager
from signal_client.services.message_parser import MessageParser
from typing import cast

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
    dead_letter_queue: DeadLetterQueue | None = None
    checkpoint_store: IngestCheckpointStore | None = None
    lock_manager: LockManager | None = None
    queue_depth_getter: Callable[[], int] | None = None


class Worker:
    def __init__(
        self, config: WorkerConfig, worker_id: int = 0, shard_id: int = 0
    ) -> None:
        self._context_factory = config.context_factory
        self._queue = config.queue
        self._message_parser = config.message_parser
        self._router = config.router
        self._middleware: list[MiddlewareCallable] = list(config.middleware)
        self._stop = asyncio.Event()
        self._worker_id = worker_id
        self._shard_id = shard_id
        self._dead_letter_queue = config.dead_letter_queue
        self._checkpoint_store = config.checkpoint_store
        self._lock_manager = config.lock_manager
        self._queue_depth_getter = config.queue_depth_getter

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
                        shard_id=self._shard_id,
                        queue_depth=self._queue.qsize(),
                    )
                    message = queued_message.message or self._message_parser.parse(
                        queued_message.raw
                    )
                    if message:
                        await self.process(message, latency, queued_message=queued_message)
                        MESSAGES_PROCESSED.inc()
                except UnsupportedMessageError as error:
                    log.debug(
                        "worker.unsupported_message: Unsupported message", error=error
                    )
                    ERRORS_OCCURRED.inc()
                except (json.JSONDecodeError, KeyError):
                    log.exception(
                        "worker.message_parse_failed: Failed to parse message",
                        raw_message=queued_message.raw,
                        worker_id=self._worker_id,
                    )
                    await self._send_to_dlq(
                        reason="parse_failed",
                        raw=queued_message.raw,
                        metadata={"worker_id": self._worker_id},
                    )
                    ERRORS_OCCURRED.inc()
                finally:
                    self._queue.task_done()
                    self._acknowledge(queued_message)
                    queue_depth = (
                        self._queue_depth_getter()
                        if self._queue_depth_getter
                        else self._queue.qsize()
                    )
                    MESSAGE_QUEUE_DEPTH.set(queue_depth)
                    SHARD_QUEUE_DEPTH.labels(shard=str(self._shard_id)).set(
                        self._queue.qsize()
                    )
                    structlog.contextvars.clear_contextvars()
            except asyncio.TimeoutError:  # noqa: PERF203
                continue

    async def process(  # compatibility alias for legacy tests/callers
        self,
        message: Message,
        queue_latency: float | None = None,
        *,
        queued_message: QueuedMessage | None = None,
    ) -> None:
        structlog.contextvars.bind_contextvars(
            message_id=message.id,
            source=message.source,
            timestamp=message.timestamp,
        )
        if await self._is_duplicate(message):
            log.debug(
                "worker.duplicate_suppressed: Duplicate message suppressed",
                message_id=str(message.id),
                source=message.source,
                timestamp=message.timestamp,
            )
            return
        recipient = message.recipient()
        if recipient:
            structlog.contextvars.bind_contextvars(conversation_id=recipient)
        if self._lock_manager and recipient:
            async with self._lock_manager.lock(recipient):
                await self._dispatch_message(
                    message,
                    queue_latency,
                    queued_message=queued_message,
                )
            return

        await self._dispatch_message(
            message,
            queue_latency,
            queued_message=queued_message,
        )

    async def _dispatch_message(
        self,
        message: Message,
        queue_latency: float | None = None,
        *,
        queued_message: QueuedMessage | None = None,
    ) -> None:
        recipient = message.recipient()
        context = self._context_factory(message)
        text = context.message.message
        if not isinstance(text, str) or not text:
            log.debug(
                "worker.message_no_text: Message has no text",
                message_id=str(message.id),
                recipient=recipient,
                source=message.source,
            )
            await self._mark_checkpoint(message, queued_message)
            return

        command, trigger = self._router.match(text)
        if command is None:
            log.debug(
                "worker.command_not_found: Command not found",
                trigger=trigger,
                message_id=str(message.id),
                recipient=recipient,
            )
            await self._mark_checkpoint(message, queued_message)
            return
        if not self._is_whitelisted(command, context):
            log.debug(
                "worker.command_not_whitelisted: Command not whitelisted",
                command=command.__class__.__name__,
                recipient=recipient,
                message_id=str(message.id),
            )
            await self._mark_checkpoint(message, queued_message)
            return

        handler = getattr(command, "handle", None)
        handler_name = getattr(handler, "__name__", command.__class__.__name__)
        status = "success"
        start_time = time.perf_counter()
        try:
            structlog.contextvars.bind_contextvars(
                command_name=handler_name,
                worker_id=self._worker_id,
                shard_id=self._shard_id,
                queue_latency=queue_latency,
            )
            await self._execute_with_middleware(command, context)
            await self._mark_checkpoint(message, queued_message)
        except SignalAPIError as error:
            status = "failure"
            await self._handle_api_exception(
                error=error,
                handler_name=handler_name,
                trigger=trigger,
                message=message,
                recipient=recipient,
                queued_message=queued_message,
            )
        except Exception:
            status = "failure"
            log.exception(
                "worker.command_failed: Command failed",
                command_name=handler_name,
                trigger=trigger,
                worker_id=self._worker_id,
                shard_id=self._shard_id,
                queue_latency=queue_latency,
                message_id=str(message.id),
            )
            await self._send_to_dlq(
                reason="command_failed",
                raw=queued_message.raw if queued_message else None,
                metadata=self._build_dlq_metadata(
                    handler_name=handler_name,
                    trigger=trigger,
                    message=message,
                    recipient=recipient,
                ),
            )
            ERRORS_OCCURRED.inc()
        finally:
            duration = time.perf_counter() - start_time
            COMMAND_LATENCY.labels(
                command=handler_name, status=status
            ).observe(duration)
            COMMANDS_PROCESSED.labels(
                command=handler_name, status=status
            ).inc()

    async def _handle_api_exception(
        self,
        *,
        error: SignalAPIError,
        handler_name: str,
        trigger: str | None,
        message: Message,
        recipient: str | None,
        queued_message: QueuedMessage | None,
    ) -> None:
        metadata = self._build_dlq_metadata(
            handler_name=handler_name,
            trigger=trigger,
            message=message,
            recipient=recipient,
        )
        metadata.update(
            {
                "status_code": getattr(error, "status_code", None),
                "error_type": error.__class__.__name__,
                "error_message": str(error),
            }
        )
        reason = "api_error"
        event = "worker.command_api_error"
        if isinstance(error, RateLimitError):
            reason = "rate_limited"
            event = "worker.command_rate_limited"
        elif isinstance(error, ServerError):
            reason = "server_error"
            event = "worker.command_server_error"
        elif isinstance(error, AuthenticationError):
            reason = "authentication_error"
            event = "worker.command_authentication_failed"
        elif isinstance(error, (InvalidRecipientError, GroupNotFoundError)):
            reason = "invalid_recipient"
            event = "worker.command_invalid_recipient"

        self._warn(
            event,
            command_name=handler_name,
            trigger=trigger,
            status_code=getattr(error, "status_code", None),
            recipient=recipient,
            message_id=str(getattr(message, "id", "")),
        )
        await self._send_to_dlq(
            reason=reason,
            raw=queued_message.raw if queued_message else None,
            metadata=metadata,
        )
        ERRORS_OCCURRED.inc()

    def _build_dlq_metadata(
        self,
        *,
        handler_name: str,
        trigger: str | None,
        message: Message,
        recipient: str | None,
    ) -> dict[str, object]:
        return {
            "command": handler_name,
            "trigger": trigger,
            "worker_id": self._worker_id,
            "shard_id": self._shard_id,
            "message_id": str(getattr(message, "id", "")),
            "source": getattr(message, "source", None),
            "recipient": recipient,
            "timestamp": getattr(message, "timestamp", None),
        }

    @staticmethod
    def _is_whitelisted(command: Command, context: Context) -> bool:
        if not command.whitelisted:
            return True
        return context.message.source in command.whitelisted

    async def _execute_with_middleware(
        self, command: Command, context: Context
    ) -> None:
        handler = command.handle
        if handler is None:
            message = "Command handler is not configured."
            raise CommandError(message)

        async def invoke(index: int, ctx: Context) -> None:
            if index >= len(self._middleware):
                await handler(ctx)
                return

            middleware_fn = self._middleware[index]

            async def next_callable(next_ctx: Context) -> None:
                await invoke(index + 1, next_ctx)

            await middleware_fn(ctx, next_callable)

        await invoke(0, context)

    async def _mark_checkpoint(
        self, message: Message, queued_message: QueuedMessage | None
    ) -> None:
        if not self._checkpoint_store:
            return
        try:
            await self._checkpoint_store.mark_processed(
                source=message.source,
                timestamp=message.timestamp,
                enqueued_at=queued_message.enqueued_at if queued_message else None,
            )
        except Exception:  # pragma: no cover - defensive
            self._warn(
                "worker.checkpoint_failed: Failed to mark checkpoint",
                source=message.source,
                timestamp=message.timestamp,
            )

    async def _is_duplicate(self, message: Message) -> bool:
        if not self._checkpoint_store:
            return False
        try:
            return await self._checkpoint_store.is_duplicate(
                source=message.source, timestamp=message.timestamp
            )
        except Exception:  # pragma: no cover - defensive
            self._warn(
                "worker.checkpoint_lookup_failed: Failed to lookup checkpoint",
                source=message.source,
                timestamp=message.timestamp,
            )
            return False

    async def _send_to_dlq(
        self,
        *,
        reason: str,
        raw: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if not self._dead_letter_queue or raw is None:
            return
        payload: dict[str, object] = {"raw": raw, "reason": reason}
        if metadata:
            payload["metadata"] = metadata
        try:
            self._warn(
                "worker.dlq_enqueued: Message enqueued to DLQ",
                reason=reason,
                worker_id=self._worker_id,
                shard_id=self._shard_id,
                message_id=(metadata or {}).get("message_id"),
                recipient=(metadata or {}).get("recipient"),
            )
            await self._dead_letter_queue.send(payload)
        except Exception:  # pragma: no cover - defensive
            self._warn(
                "worker.dlq_send_failed: Failed to send message to DLQ",
                reason=reason,
                worker_id=self._worker_id,
            )

    def _acknowledge(self, queued_message: QueuedMessage) -> None:
        ack = queued_message.ack
        if ack is None:
            return
        try:
            ack()
        except Exception:  # pragma: no cover - defensive
            self._warn(
                "worker.ack_failed: Failed to acknowledge message",
                worker_id=self._worker_id,
                shard_id=self._shard_id,
            )

    def _warn(self, event: str, **kwargs: object) -> None:
        """Emit warnings defensively in case structlog is minimally configured."""
        try:
            log.warning(event, **kwargs)
        except TypeError:
            logging.getLogger(__name__).warning("%s %s", event, kwargs)


class WorkerPool:
    def __init__(
        self,
        context_factory: Callable[[Message], Context],
        queue: asyncio.Queue[QueuedMessage],
        message_parser: MessageParser,
        *,
        router: CommandRouter | None = None,
        pool_size: int = 4,
        dead_letter_queue: DeadLetterQueue | None = None,
        checkpoint_store: IngestCheckpointStore | None = None,
        shard_count: int | None = None,
        lock_manager: LockManager | None = None,
    ) -> None:
        self._context_factory = context_factory
        self._queue = queue
        self._message_parser = message_parser
        self._router = router or CommandRouter()
        self._pool_size = pool_size
        self._shard_count = shard_count or pool_size
        self._middleware: list[MiddlewareCallable] = []
        self._middleware_ids: set[int] = set()
        self._workers: list[Worker] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._started = asyncio.Event()
        self._dead_letter_queue = dead_letter_queue
        self._checkpoint_store = checkpoint_store
        self._lock_manager = lock_manager
        self._shard_queues: list[asyncio.Queue[QueuedMessage]] = []
        self._distributor_task: asyncio.Task[None] | None = None
        self._distributor_stop = asyncio.Event()

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
        if self._pool_size <= 0:
            self._pool_size = 1
        if self._shard_count <= 0:
            self._shard_count = 1
        if self._pool_size < self._shard_count:
            raise ValueError("worker_pool_size must be >= shard_count.")

        self._initialize_shards()
        self._start_distributor()

        for worker_id in range(self._pool_size):
            shard_id = worker_id % self._shard_count
            worker_config = WorkerConfig(
                context_factory=self._context_factory,
                queue=self._shard_queues[shard_id],
                message_parser=self._message_parser,
                router=self._router,
                middleware=self._middleware,
                dead_letter_queue=self._dead_letter_queue,
                checkpoint_store=self._checkpoint_store,
                lock_manager=self._lock_manager,
                queue_depth_getter=self._queue_depth,
            )
            worker = Worker(
                worker_config,
                worker_id=worker_id,
                shard_id=shard_id,
            )
            self._workers.append(worker)
            task = asyncio.create_task(worker.process_messages())
            self._tasks.append(task)
        self._started.set()

    def stop(self) -> None:
        self._distributor_stop.set()
        for worker in self._workers:
            worker.stop()

    async def join(self) -> None:
        if self._distributor_task:
            await self._distributor_task
        if self._tasks:
            await asyncio.gather(*self._tasks)

    def _initialize_shards(self) -> None:
        if self._shard_queues:
            return
        if self._shard_count <= 0:
            self._shard_count = 1

        per_shard_size = (
            math.ceil(self._queue.maxsize / self._shard_count)
            if self._queue.maxsize > 0
            else 0
        )
        if per_shard_size <= 0 and self._queue.maxsize > 0:
            per_shard_size = 1

        self._shard_queues = [
            asyncio.Queue(maxsize=per_shard_size) for _ in range(self._shard_count)
        ]
        for index, shard_queue in enumerate(self._shard_queues):
            SHARD_QUEUE_DEPTH.labels(shard=str(index)).set(shard_queue.qsize())

    def _start_distributor(self) -> None:
        if self._distributor_task:
            return
        self._distributor_stop.clear()
        self._distributor_task = asyncio.create_task(self._distribute_messages())

    async def _distribute_messages(self) -> None:
        while True:
            if self._distributor_stop.is_set() and self._queue.empty():
                return
            try:
                queued_item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:  # noqa: PERF203
                continue

            queued_message = (
                queued_item
                if isinstance(queued_item, QueuedMessage)
                else QueuedMessage(
                    raw=str(queued_item),
                    enqueued_at=time.perf_counter(),
                )
            )
            if queued_message.message is None:
                queued_message.message = self._message_parser.parse(
                    queued_message.raw
                )

            recipient = queued_message.recipient
            if queued_message.message:
                recipient = queued_message.message.recipient()
            elif recipient is None:
                recipient = self._message_parser.recipient_from_raw(
                    queued_message.raw
                )
            queued_message.recipient = recipient

            if queued_message.ack:
                existing_ack = cast(Callable[[], None], queued_message.ack)

                def _combined_ack(existing_ack=existing_ack) -> None:
                    existing_ack()
                    self._queue.task_done()

                queued_message.ack = _combined_ack
            else:
                queued_message.ack = self._queue.task_done

            shard_index = self._compute_shard(recipient)

            try:
                await self._shard_queues[shard_index].put(queued_message)
            except Exception:
                log.exception(
                    "worker_pool.shard_enqueue_failed: Failed to enqueue message to shard",
                    shard_id=shard_index,
                )
                try:
                    self._queue.task_done()
                except Exception:  # pragma: no cover - defensive
                    pass
            else:
                self._set_queue_depth_metric()

    def _compute_shard(self, recipient: str | None) -> int:
        if not self._shard_queues:
            return 0
        if not recipient:
            return 0
        shard_index = crc32(recipient.encode("utf-8")) % len(self._shard_queues)
        return shard_index

    def _queue_depth(self) -> int:
        shard_depth = sum(queue.qsize() for queue in self._shard_queues)
        return self._queue.qsize() + shard_depth

    def _set_queue_depth_metric(self) -> None:
        MESSAGE_QUEUE_DEPTH.set(self._queue_depth())
        for index, shard_queue in enumerate(self._shard_queues):
            SHARD_QUEUE_DEPTH.labels(shard=str(index)).set(shard_queue.qsize())


__all__ = [
    "CommandRouter",
    "MiddlewareCallable",
    "Worker",
    "WorkerConfig",
    "WorkerPool",
]
