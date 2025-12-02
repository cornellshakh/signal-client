import json
from typing import Any

import redis.asyncio as redis

from .base import Storage, StorageError


class RedisStorage(Storage):
    def __init__(self, host: str, port: int) -> None:
        self._redis: redis.Redis = redis.Redis(host=host, port=port, db=0)

    @property
    def client(self) -> redis.Redis:
        """Expose the underlying Redis client for testing purposes."""
        return self._redis

    async def close(self) -> None:
        await self._redis.close()

    async def append(self, key: str, data: dict[str, Any]) -> None:
        try:
            object_str = json.dumps(data)
            await self._redis.rpush(key, object_str)  # type: ignore[misc]
        except (redis.RedisError, TypeError) as e:
            msg = f"Redis append failed: {e}"
            raise StorageError(msg) from e

    async def read_all(self, key: str) -> list[dict[str, Any]]:
        try:
            result_bytes = await self._redis.lrange(key, 0, -1)  # type: ignore[misc]
            return [json.loads(item.decode("utf-8")) for item in result_bytes]
        except (redis.RedisError, TypeError, json.JSONDecodeError) as e:
            msg = f"Redis read_all failed: {e}"
            raise StorageError(msg) from e

    async def delete_all(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except redis.RedisError as e:
            msg = f"Redis delete_all failed: {e}"
            raise StorageError(msg) from e
