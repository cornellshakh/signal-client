"""Durable checkpointing for websocket ingest to drop duplicates and resume.

This module provides an IngestCheckpointStore for persisting a sliding window
of recently processed (source, timestamp) pairs, used for deduplication
and resuming after restarts.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import structlog

from signal_client.adapters.storage.base import Storage

log = structlog.get_logger()


@dataclass
class CheckpointRecord:
    """Represents a processed message for checkpointing."""

    source: str
    timestamp: int
    enqueued_at: float


class IngestCheckpointStore:
    """Durable checkpointing for websocket ingest to drop duplicates and resume.

    We persist a sliding window of recently processed (source, timestamp) pairs.
    This is intentionally coarse but sufficient to dedupe Signal replayed
    envelopes after reconnects or process crashes. The window bounds growth so
    SQLite-backed bots remain lightweight.
    """

    def __init__(
        self,
        storage: Storage,
        key: str,
        *,
        window_size: int = 5000,
    ) -> None:
        """Initialize an IngestCheckpointStore instance.

        Args:
            storage: The storage backend to use for persistence.
            key: The key under which to store checkpoint records.
            window_size: The maximum number of records to keep in the sliding window.

        """
        self._storage = storage
        self._key = key
        self._window_size = max(1, window_size)
        self._records: list[CheckpointRecord] = []
        self._lock = asyncio.Lock()
        self._loaded = False

    async def load(self) -> None:
        """Load the last persisted window from storage."""
        async with self._lock:
            if self._loaded:
                return
            records = await self._storage.read_all(self._key)
            if records:
                parsed = [
                    self._deserialize(record)
                    for record in records
                    if isinstance(record, dict)
                ]
                self._records = [rec for rec in parsed if rec is not None]
                log.info(
                    "ingest_checkpoint.loaded",
                    key=self._key,
                    count=len(self._records),
                )
            self._loaded = True

    async def mark_processed(
        self,
        source: str,
        timestamp: int,
        *,
        enqueued_at: float | None = None,
    ) -> None:
        """Persist the processed message for deduplication."""
        await self.load()
        record = CheckpointRecord(
            source=source,
            timestamp=timestamp,
            enqueued_at=enqueued_at or time.time(),
        )
        async with self._lock:
            self._records.append(record)
            if len(self._records) > self._window_size:
                overflow = len(self._records) - self._window_size
                del self._records[0:overflow]
            await self._persist_locked()

    async def is_duplicate(self, source: str, timestamp: int) -> bool:
        """Return True if the message was processed recently."""
        await self.load()
        async with self._lock:
            for record in reversed(self._records):
                if record.source == source and record.timestamp == timestamp:
                    return True
        return False

    async def compact_before(self, cutoff_timestamp: int) -> None:
        """Drop checkpoints older than the cutoff to prevent unbounded growth."""
        await self.load()
        async with self._lock:
            retained = [
                record
                for record in self._records
                if record.timestamp >= cutoff_timestamp
            ]
            if len(retained) == len(self._records):
                return
            self._records = retained
            await self._persist_locked()

    async def _persist_locked(self) -> None:
        await self._storage.delete_all(self._key)
        for record in self._records:
            await self._storage.append(self._key, self._serialize(record))
        log.debug(
            "ingest_checkpoint.persisted",
            key=self._key,
            count=len(self._records),
        )

    def _serialize(self, record: CheckpointRecord) -> dict[str, Any]:
        return {
            "source": record.source,
            "timestamp": record.timestamp,
            "enqueued_at": record.enqueued_at,
        }

    @staticmethod
    def _deserialize(record: dict[str, Any]) -> CheckpointRecord | None:
        try:
            source = str(record["source"])
            timestamp = int(record["timestamp"])
            enqueued_at_raw = record.get("enqueued_at", time.time())
            enqueued_at = float(enqueued_at_raw)
        except (KeyError, TypeError, ValueError):
            log.debug("ingest_checkpoint.invalid_record", record=record)
            return None
        return CheckpointRecord(
            source=source,
            timestamp=timestamp,
            enqueued_at=enqueued_at,
        )


__all__ = ["CheckpointRecord", "IngestCheckpointStore"]
