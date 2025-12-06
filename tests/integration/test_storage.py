"""Integration tests for storage backends."""

from __future__ import annotations

import pytest

from signal_client.adapters.storage.redis import RedisStorage
from signal_client.adapters.storage.sqlite import SQLiteStorage
from signal_client.app import Application
from signal_client.core.config import Settings


@pytest.mark.asyncio
async def test_sqlite_storage_integration(tmp_path):
    """Test SQLite storage integration."""
    database_path = tmp_path / "test.db"
    storage = SQLiteStorage(database=str(database_path))

    message = {"id": 1, "body": "hello"}

    await storage.append("dlq", message)
    stored = await storage.read_all("dlq")
    assert stored == [message]

    await storage.delete_all("dlq")
    assert await storage.read_all("dlq") == []

    await storage.close()


@pytest.mark.asyncio
async def test_application_sqlite_configuration(tmp_path):
    """Test application with SQLite storage configuration."""
    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "storage_type": "sqlite",
        "sqlite_database": str(tmp_path / "signal_client.db"),
    }

    app = Application(Settings.from_sources(config=config))

    storage = app.storage
    try:
        assert isinstance(storage, SQLiteStorage)
        await storage.append("queue", {"data": 1})
        await storage.delete_all("queue")
    finally:
        await storage.close()
        await app.shutdown()


@pytest.mark.asyncio
async def test_application_redis_configuration(monkeypatch):
    """Test application with Redis storage configuration."""

    class FakeRedis:
        def __init__(self, *_, **__):
            self._data: dict[str, list[bytes]] = {}

        async def rpush(self, key: str, value: str) -> None:
            self._data.setdefault(key, []).append(value.encode("utf-8"))

        async def lrange(self, key: str, *_):
            return self._data.get(key, [])

        async def delete(self, key: str) -> None:
            self._data.pop(key, None)

        async def close(self) -> None:
            return None

    monkeypatch.setattr("redis.asyncio.Redis", FakeRedis)

    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "storage_type": "redis",
        "redis_host": "localhost",
        "redis_port": 6379,
    }

    app = Application(Settings.from_sources(config=config))

    storage = app.storage
    try:
        assert isinstance(storage, RedisStorage)
        await storage.append("queue", {"value": 1})
        entries = await storage.read_all("queue")
        assert entries == [{"value": 1}]
        await storage.delete_all("queue")
    finally:
        await storage.close()
        await app.shutdown()
