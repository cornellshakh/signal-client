from __future__ import annotations

import copy
import time
from collections import defaultdict
from typing import Any

import pytest

from signal_client.infrastructure.storage.base import Storage
from signal_client.metrics import DLQ_BACKLOG
from signal_client.services.dead_letter_queue import DeadLetterQueue


class InMemoryStorage(Storage):
    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def exists(self, key: str) -> bool:
        return bool(self._data.get(key))

    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        values = self._data.get(key)
        if values is None:
            raise KeyError(key)
        if len(values) == 1:
            return copy.deepcopy(values[0])
        return copy.deepcopy(values)

    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        if isinstance(data, list):
            self._data[key] = [copy.deepcopy(item) for item in data]
        else:
            self._data[key] = [copy.deepcopy(data)]

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def close(self) -> None:  # pragma: no cover - nothing to close
        return None

    async def append(self, key: str, data: dict[str, Any]) -> None:
        self._data[key].append(copy.deepcopy(data))

    async def read_all(self, key: str) -> list[dict[str, Any]]:
        return [copy.deepcopy(item) for item in self._data.get(key, [])]

    async def delete_all(self, key: str) -> None:
        self._data[key] = []


@pytest.mark.asyncio
async def test_replay_preserves_retry_count_for_pending_messages() -> None:
    storage = InMemoryStorage()
    queue_name = "dlq"
    future_time = time.time() + 5
    message = {
        "message": {"id": 1},
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
    storage = InMemoryStorage()
    queue_name = "dlq"
    past_time = time.time() - 1
    message = {
        "message": {"id": 2},
        "retry_count": 1,
        "next_retry_at": past_time,
    }
    await storage.append(queue_name, message)

    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    ready_messages = await dlq.replay()

    assert ready_messages == [{"id": 2}]
    stored_messages = await storage.read_all(queue_name)
    assert stored_messages == []


@pytest.mark.asyncio
async def test_replay_discards_messages_over_retry_limit() -> None:
    storage = InMemoryStorage()
    queue_name = "dlq"
    message = {
        "message": {"id": 3},
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
    storage = InMemoryStorage()
    queue_name = "dlq"
    dlq = DeadLetterQueue(storage, queue_name, max_retries=5)

    await dlq.send({"id": 1})
    gauge = DLQ_BACKLOG.labels(queue=queue_name)
    assert gauge._value.get() == 1  # type: ignore[attr-defined]

    await dlq.replay()
    assert gauge._value.get() == 0  # type: ignore[attr-defined]
