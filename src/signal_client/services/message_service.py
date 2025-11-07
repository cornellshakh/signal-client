from __future__ import annotations

import asyncio
import json
import time

import structlog

from signal_client.infrastructure.websocket_client import WebSocketClient
from signal_client.metrics import MESSAGE_QUEUE_DEPTH
from signal_client.services.dead_letter_queue import DeadLetterQueue
from signal_client.services.models import QueuedMessage

log = structlog.get_logger()


class MessageService:
    def __init__(
        self,
        websocket_client: WebSocketClient,
        queue: asyncio.Queue[QueuedMessage],
        dead_letter_queue: DeadLetterQueue | None = None,
        *,
        enqueue_timeout: float = 1.0,
        drop_oldest_on_timeout: bool = True,
    ) -> None:
        self._websocket_client = websocket_client
        self._queue = queue
        self._dead_letter_queue = dead_letter_queue
        self._enqueue_timeout = max(0.0, enqueue_timeout)
        self._drop_oldest_on_timeout = drop_oldest_on_timeout
        self._started = asyncio.Event()

    async def listen(self) -> None:
        """Listen for incoming messages and process them."""
        self._started.set()
        async for raw_message in self._websocket_client.listen():
            queued_message = QueuedMessage(
                raw=raw_message, enqueued_at=time.perf_counter()
            )
            try:
                enqueued = await self._enqueue_with_backpressure(queued_message)
            except Exception:
                log.exception("message_service.enqueue_failed")
                enqueued = False

            if enqueued:
                self._update_queue_depth_metric()
                continue

            log.warning(
                "message_service.queue_full",
                queue_depth=self._queue.qsize(),
                queue_maxsize=self._queue.maxsize,
            )
            if self._dead_letter_queue:
                parsed_message = self._parse_for_dlq(raw_message)
                await self._dead_letter_queue.send(parsed_message)

    async def _enqueue_with_backpressure(self, queued_message: QueuedMessage) -> bool:
        try:
            await asyncio.wait_for(
                self._queue.put(queued_message),
                timeout=self._enqueue_timeout,
            )
        except asyncio.TimeoutError:
            return await self._handle_enqueue_timeout(queued_message)
        return True

    async def _handle_enqueue_timeout(self, queued_message: QueuedMessage) -> bool:
        if not self._drop_oldest_on_timeout:
            return False

        try:
            _ = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return False

        self._queue.task_done()
        log.warning(
            "message_service.dropped_oldest",
            queue_depth=self._queue.qsize(),
            queue_maxsize=self._queue.maxsize,
        )
        self._update_queue_depth_metric()

        try:
            await asyncio.wait_for(
                self._queue.put(queued_message),
                timeout=self._enqueue_timeout,
            )
        except asyncio.TimeoutError:
            self._update_queue_depth_metric()
            log.warning(
                "message_service.queue_full_after_drop",
                queue_depth=self._queue.qsize(),
                queue_maxsize=self._queue.maxsize,
            )
            return False

        self._update_queue_depth_metric()
        return True

    @staticmethod
    def _parse_for_dlq(raw_message: str) -> dict | str:
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError:
            return {"raw": raw_message}

    def _update_queue_depth_metric(self) -> None:
        MESSAGE_QUEUE_DEPTH.set(self._queue.qsize())
