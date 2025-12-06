from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import structlog

if TYPE_CHECKING:
    from signal_client.adapters.storage.base import Storage

from signal_client.observability.logging import safe_log
from signal_client.observability.metrics import DLQ_BACKLOG, DLQ_EVENTS

log = structlog.get_logger()


@dataclass
class DLQEntry:
    payload: dict[str, Any] | str
    retry_count: int
    next_retry_at: float

    def to_record(self) -> dict[str, Any]:
        return {
            "payload": self.payload,
            # Preserve legacy 'message' key for compatibility with existing
            # DLQ consumers.
            "message": self.payload,
            "retry_count": self.retry_count,
            "next_retry_at": self.next_retry_at,
        }

    @classmethod
    def from_record(
        cls,
        record: dict[str, Any],
        *,
        default_next_retry_at: float,
    ) -> DLQEntry:
        payload_raw = record.get("payload")
        if payload_raw is None:
            payload_raw = record.get("message", {})
        payload = cast("dict[str, Any] | str", payload_raw)
        retry_count = int(record.get("retry_count", 0))
        next_retry_at = float(record.get("next_retry_at", default_next_retry_at))
        return cls(
            payload=payload,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
        )


class DeadLetterQueue:
    def __init__(
        self,
        storage: Storage,
        queue_name: str,
        max_retries: int = 5,
        *,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 300.0,
    ) -> None:
        self._storage = storage
        self._queue_name = queue_name
        self._max_retries = max_retries
        self._base_backoff_seconds = max(0.0, base_backoff_seconds)
        self._max_backoff_seconds = max(self._base_backoff_seconds, max_backoff_seconds)

    async def send(
        self,
        message: dict[str, Any] | str,
        *,
        retry_count: int = 0,
        next_retry_at: float | None = None,
    ) -> None:
        if retry_count < 0:
            message = "retry_count cannot be negative"
            raise ValueError(message)
        scheduled_for = (
            next_retry_at
            if next_retry_at is not None
            else self._compute_next_retry_at(retry_count)
        )
        entry = DLQEntry(
            payload=message,
            retry_count=retry_count,
            next_retry_at=scheduled_for,
        )
        await self._storage.append(self._queue_name, entry.to_record())
        safe_log(
            log,
            "debug",
            "DLQ message enqueued",
            event_slug="dlq.message_enqueued",
            queue=self._queue_name,
            retry_count=retry_count,
            next_retry_at=scheduled_for,
        )
        DLQ_EVENTS.labels(queue=self._queue_name, event="enqueued").inc()
        await self._update_backlog_metric()

    async def inspect(self) -> list[dict[str, Any]]:
        """Return all DLQ entries without mutating the queue."""
        return await self._storage.read_all(self._queue_name)

    async def replay(self) -> list[dict[str, Any]]:
        messages = await self._storage.read_all(self._queue_name)
        if not messages:
            return []

        await self._storage.delete_all(self._queue_name)

        ready_messages: list[dict[str, Any]] = []
        messages_to_keep: list[dict[str, Any]] = []
        current_time = time.time()

        for msg in messages:
            entry = DLQEntry.from_record(msg, default_next_retry_at=current_time)
            if entry.retry_count >= self._max_retries:
                DLQ_EVENTS.labels(queue=self._queue_name, event="discarded").inc()
                safe_log(
                    log,
                    "warning",
                    "DLQ message discarded due to retry limit",
                    event_slug="dlq.message_discarded",
                    queue=self._queue_name,
                    retry_count=entry.retry_count,
                )
                continue

            if entry.next_retry_at <= current_time:
                updated_retry_count = entry.retry_count + 1
                ready_messages.append(
                    DLQEntry(
                        payload=entry.payload,
                        retry_count=updated_retry_count,
                        next_retry_at=self._compute_next_retry_at(updated_retry_count),
                    ).to_record()
                )
            else:
                messages_to_keep.append(entry.to_record())

        for msg in messages_to_keep:
            await self._storage.append(self._queue_name, msg)
            safe_log(
                log,
                "debug",
                "DLQ message pending",
                event_slug="dlq.message_pending",
                queue=self._queue_name,
                retry_count=msg.get("retry_count", 0),
                available_in=max(
                    msg.get("next_retry_at", current_time) - current_time,
                    0,
                ),
            )
            DLQ_EVENTS.labels(queue=self._queue_name, event="pending").inc()

        await self._update_backlog_metric(len(messages_to_keep))

        if ready_messages:
            safe_log(
                log,
                "info",
                "DLQ messages ready for replay",
                event_slug="dlq.messages_ready",
                queue=self._queue_name,
                count=len(ready_messages),
            )
        DLQ_EVENTS.labels(queue=self._queue_name, event="ready").inc(
            len(ready_messages)
        )

        return ready_messages

    async def _update_backlog_metric(self, count: int | None = None) -> None:
        if count is None:
            entries = await self._storage.read_all(self._queue_name)
            count = len(entries)
        DLQ_BACKLOG.labels(queue=self._queue_name).set(count)

    def _compute_next_retry_at(self, retry_count: int) -> float:
        delay = self._base_backoff_seconds * (2**retry_count)
        bounded_delay = min(delay, self._max_backoff_seconds)
        return time.time() + bounded_delay
