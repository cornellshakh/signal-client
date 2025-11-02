from __future__ import annotations

from typing import Any

from signal_client.infrastructure.storage.base import Storage
from signal_client.infrastructure.storage.redis import RedisStorage
from signal_client.infrastructure.storage.sqlite import SQLiteStorage


class StorageService:
    def __init__(self, config: dict[str, Any]) -> None:
        storage_type = config.get("type", "in-memory")
        if storage_type == "sqlite":
            self._storage: Storage = SQLiteStorage(config["sqlite_db"])
        elif storage_type == "redis":
            self._storage = RedisStorage(config["redis_host"], config["redis_port"])
        else:
            self._storage = SQLiteStorage()  # In-memory SQLite

    async def exists(self, key: str) -> bool:
        return await self._storage.exists(key)

    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        return await self._storage.read(key)

    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        await self._storage.save(key, data)

    async def delete(self, key: str) -> None:
        await self._storage.delete(key)

    async def close(self) -> None:
        await self._storage.close()
