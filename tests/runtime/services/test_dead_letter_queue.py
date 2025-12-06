"""Tests for the dead letter queue service."""

from __future__ import annotations

import copy
import time
from collections import defaultdict
from typing import Any

import pytest

from signal_client.adapters.storage.base import Storage
from signal_client.observability.metrics import DLQ_BACKLOG, DLQ_EVENTS
from signal_client.runtime.services.dead_letter_queue import DeadLetterQueue


def _counter_value(counter, **labels):
    return counter.labels(**labels)._value.get()  # type: ignore[attr-defined]


class InMemoryStorage(Storage):
    """An in-memory implementation of the Storage interface for testing."""

    def __init__(self) -> None:
        """Initialize the InMemoryStorage."""
        self._data: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def close(self) -> None:  # pragma: no cover - nothing to close
        """Close the storage (no-op for in-memory)."""
        return

    async def append(self, key: str, data: dict[str, Any]) -> None:
        """Append data to a list associated with a key."""
        self._data[key].append(copy.deepcopy(data))

    async def read_all(self, key: str) -> list[dict[str, Any]]:
        """Read all data associated with a key."""
        return [copy.deepcopy(item) for item in self._data.get(key, [])]

    async def delete_all(self, key: str) -> None:
        """Delete all data associated with a key."""
        self._data[key] = []


@pytest.mark.asyncio
async def test_replay_preserves_retry_count_for_pending_messages() -> None:
    """Test that replay preserves retry count for messages not yet ready."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    future_time = time.time() + 5
    message = {
        "payload": {"id": 1},
        "retry_count": 2,
        "next_retry_at": future_time,
    }
    await storage.append(queue_name, message)

    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    ready_messages = await dlq.replay()

    assert ready_messages == []
    stored_messages = await storage.read_all(queue_name)
    assert len(stored_messages) == 1
    stored_message = stored_messages[0]
    assert stored_message["retry_count"] == 2
    assert stored_message["next_retry_at"] == pytest.approx(
        future_time, rel=0, abs=0.01
    )


@pytest.mark.asyncio
async def test_replay_returns_ready_messages_and_clears_them() -> None:
    """Test that replay returns ready messages and clears them from storage."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    past_time = time.time() - 1
    message = {
        "payload": {"id": 2},
        "retry_count": 1,
        "next_retry_at": past_time,
    }
    await storage.append(queue_name, message)

    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    ready_messages = await dlq.replay()

    assert len(ready_messages) == 1
    ready_entry = ready_messages[0]
    assert ready_entry["payload"] == {"id": 2}
    assert ready_entry["retry_count"] == 2
    assert ready_entry["next_retry_at"] > time.time()
    stored_messages = await storage.read_all(queue_name)
    assert stored_messages == []


@pytest.mark.asyncio
async def test_replay_handles_legacy_message_field() -> None:
    """Test that replay correctly handles legacy message field structure."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    legacy_message = {
        "message": {"id": 42},
        "retry_count": 0,
        "next_retry_at": time.time() - 1,
    }
    await storage.append(queue_name, legacy_message)

    dlq = DeadLetterQueue(storage, queue_name, max_retries=2)

    ready_messages = await dlq.replay()

    assert len(ready_messages) == 1
    assert ready_messages[0]["payload"] == {"id": 42}


@pytest.mark.asyncio
async def test_replay_discards_messages_over_retry_limit() -> None:
    """Test that replay discards messages that have exceeded the retry limit."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    message = {
        "payload": {"id": 3},
        "retry_count": 5,
        "next_retry_at": time.time() - 1,
    }
    await storage.append(queue_name, message)

    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    ready_messages = await dlq.replay()

    assert ready_messages == []
    stored_messages = await storage.read_all(queue_name)
    assert stored_messages == []


@pytest.mark.asyncio
async def test_dlq_updates_backlog_metric() -> None:
    """Test that the DLQ updates its backlog metric."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    dlq = DeadLetterQueue(storage, queue_name, max_retries=5, base_backoff_seconds=0.0)

    enqueued_before = _counter_value(DLQ_EVENTS, queue=queue_name, event="enqueued")
    ready_before = _counter_value(DLQ_EVENTS, queue=queue_name, event="ready")

    await dlq.send({"id": 1})
    gauge = DLQ_BACKLOG.labels(queue=queue_name)
    assert gauge._value.get() == 1  # type: ignore[attr-defined]
    assert (
        _counter_value(DLQ_EVENTS, queue=queue_name, event="enqueued")
        == enqueued_before + 1
    )

    await dlq.replay()
    assert gauge._value.get() == 0  # type: ignore[attr-defined]
    assert (
        _counter_value(DLQ_EVENTS, queue=queue_name, event="ready") == ready_before + 1
    )


@pytest.mark.asyncio
async def test_send_honors_custom_retry_metadata() -> None:
    """Test that send honors custom retry metadata."""
    storage = InMemoryStorage()
    queue_name = "dlq"
    future_time = time.time() + 10
    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    await dlq.send({"id": 99}, retry_count=3, next_retry_at=future_time)
    stored_messages = await storage.read_all(queue_name)
    assert stored_messages[0]["retry_count"] == 3
    assert stored_messages[0]["next_retry_at"] == pytest.approx(
        future_time, rel=0, abs=0.01
    )
