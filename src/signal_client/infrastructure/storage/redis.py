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

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        try:
            result_bytes = await self._redis.hgetall(key)  # type: ignore[misc]
            if not result_bytes:
                msg = f"Key '{key}' not found in Redis storage."
                raise StorageError(msg)

            if b"__list__" in result_bytes:
                list_payload = json.loads(result_bytes[b"__list__"].decode("utf-8"))
                if isinstance(list_payload, list):
                    return list_payload
                msg = "Redis stored list payload is corrupted."
                raise StorageError(msg)

            return {
                k.decode("utf-8"): json.loads(v.decode("utf-8"))
                for k, v in result_bytes.items()
            }
        except (redis.RedisError, TypeError, json.JSONDecodeError) as e:
            msg = f"Redis load failed: {e}"
            raise StorageError(msg) from e

    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        try:
            if isinstance(data, list):
                serialized_data = {"__list__": json.dumps(data)}
            else:
                serialized_data = {k: json.dumps(v) for k, v in data.items()}
            if not serialized_data:
                await self._redis.delete(key)
                return

            await self._redis.hset(key, mapping=serialized_data)  # type: ignore[misc]
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
