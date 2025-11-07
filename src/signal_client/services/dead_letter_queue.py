from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from signal_client.infrastructure.storage.base import Storage

from signal_client.metrics import DLQ_BACKLOG

log = structlog.get_logger()


class DeadLetterQueue:
    def __init__(self, storage: Storage, queue_name: str, max_retries: int = 5) -> None:
        self._storage = storage
        self._queue_name = queue_name
        self._max_retries = max_retries

    async def send(self, message: dict[str, Any]) -> None:
        dlq_message = {
            "message": message,
            "retry_count": 0,
            "next_retry_at": time.time(),
        }
        await self._storage.append(self._queue_name, dlq_message)
        log.info(
            "dlq.message_enqueued",
            queue=self._queue_name,
            retry_count=0,
        )
        await self._update_backlog_metric()

    async def replay(self) -> list[dict[str, Any]]:
        messages = await self._storage.read_all(self._queue_name)
        if not messages:
            return []

        await self._storage.delete_all(self._queue_name)

        ready_messages: list[dict[str, Any]] = []
        messages_to_keep: list[dict[str, Any]] = []
        current_time = time.time()

        for msg in messages:
            retry_count = msg.get("retry_count", 0)
            if retry_count >= self._max_retries:
                log.warning(
                    "dlq.message_discarded",
                    queue=self._queue_name,
                    retry_count=retry_count,
                )
                continue

            next_retry_at = msg.get("next_retry_at", current_time)
            if next_retry_at <= current_time:
                ready_messages.append(msg["message"])
            else:
                messages_to_keep.append(msg)

        for msg in messages_to_keep:
            await self._storage.append(self._queue_name, msg)
            log.debug(
                "dlq.message_pending",
                queue=self._queue_name,
                retry_count=msg.get("retry_count", 0),
                available_in=max(
                    msg.get("next_retry_at", current_time) - current_time, 0
                ),
            )

        await self._update_backlog_metric(len(messages_to_keep))

        if ready_messages:
            log.info(
                "dlq.messages_ready",
                queue=self._queue_name,
                count=len(ready_messages),
            )

        return ready_messages

    async def inspect(self) -> list[dict[str, Any]]:
        return await self._storage.read_all(self._queue_name)

    async def _update_backlog_metric(self, count: int | None = None) -> None:
        if count is None:
            entries = await self._storage.read_all(self._queue_name)
            count = len(entries)
        DLQ_BACKLOG.labels(queue=self._queue_name).set(count)
