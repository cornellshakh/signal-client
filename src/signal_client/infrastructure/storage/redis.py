import json
from typing import Any

import redis.asyncio as redis

from .base import Storage, StorageError


class RedisStorage(Storage):
    def __init__(self, host: str, port: int) -> None:
        self._redis: redis.Redis = redis.Redis(host=host, port=port, db=0)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        try:
            result_bytes = await self._redis.get(key)
            if result_bytes is None:
                msg = f"Key '{key}' not found in Redis storage."
                raise StorageError(msg)
            result_str = result_bytes.decode("utf-8")
            return json.loads(result_str)
        except (redis.RedisError, TypeError, json.JSONDecodeError) as e:
            msg = f"Redis load failed: {e}"
            raise StorageError(msg) from e

    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        try:
            object_str = json.dumps(data)
            await self._redis.set(key, object_str)
        except (redis.RedisError, TypeError) as e:
            msg = f"Redis save failed: {e}"
            raise StorageError(msg) from e

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except redis.RedisError as e:
            msg = f"Redis delete failed: {e}"
            raise StorageError(msg) from e

    async def close(self) -> None:
        await self._redis.close()
