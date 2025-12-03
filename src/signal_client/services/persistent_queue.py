from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import structlog

from signal_client.storage.base import Storage

log = structlog.get_logger()


@dataclass(slots=True)
class PersistentQueuedMessage:
    raw: str
    enqueued_at: float

    def to_record(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "enqueued_at": self.enqueued_at,
        }

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "PersistentQueuedMessage | None":
        raw = record.get("raw")
        enqueued_at = record.get("enqueued_at")
        if not isinstance(raw, str):
            return None
        try:
            enqueued_at_f = float(enqueued_at)
        except (TypeError, ValueError):
            enqueued_at_f = time.time()
        return cls(raw=raw, enqueued_at=enqueued_at_f)


class PersistentQueue:
    """Optional durable backing store for ingest to survive restarts."""

    def __init__(
        self,
        storage: Storage,
        key: str,
        *,
        max_length: int = 10000,
    ) -> None:
        self._storage = storage
        self._key = key
        self._max_length = max(1, max_length)
        self._lock = asyncio.Lock()

    async def replay(self) -> list[PersistentQueuedMessage]:
        """Load persisted messages in FIFO order."""
        async with self._lock:
            records = await self._storage.read_all(self._key)
            messages: list[PersistentQueuedMessage] = []
            for record in records:
                if not isinstance(record, dict):
                    continue
                parsed = PersistentQueuedMessage.from_record(record)
                if parsed:
                    messages.append(parsed)
            if messages:
                log.info(
                    "persistent_queue.recovered",
                    key=self._key,
                    count=len(messages),
                )
            return messages

    async def append(self, raw: str, enqueued_at: float | None = None) -> None:
        """Persist a raw websocket message for later replay."""
        message = PersistentQueuedMessage(raw=raw, enqueued_at=enqueued_at or time.time())
        async with self._lock:
            await self._storage.append(self._key, message.to_record())
            await self._truncate_locked()

    async def compact(self, min_timestamp: int | None = None) -> None:
        """
        Drop persisted entries older than the provided message timestamp.

        This keeps the queue bounded once checkpoints advance, while still retaining
        enough history to replay in-flight items after a crash.
        """
        async with self._lock:
            records = await self._storage.read_all(self._key)
            if not records:
                return
            retained: list[dict[str, Any]] = []
            for record in records:
                parsed = (
                    PersistentQueuedMessage.from_record(record)
                    if isinstance(record, dict)
                    else None
                )
                if parsed is None:
                    continue
                if min_timestamp is None or parsed.enqueued_at >= min_timestamp:
                    retained.append(parsed.to_record())
            await self._storage.delete_all(self._key)
            for record in retained:
                await self._storage.append(self._key, record)
            log.debug(
                "persistent_queue.compacted",
                key=self._key,
                retained=len(retained),
            )

    async def clear(self) -> None:
        async with self._lock:
            await self._storage.delete_all(self._key)

    async def _truncate_locked(self) -> None:
        records = await self._storage.read_all(self._key)
        if len(records) <= self._max_length:
            return
        trimmed = records[-self._max_length :]
        await self._storage.delete_all(self._key)
        for record in trimmed:
            await self._storage.append(self._key, record)


__all__ = ["PersistentQueue", "PersistentQueuedMessage"]
