import json
from typing import Any

import aiosqlite

from .base import Storage, StorageError


class SQLiteStorage(Storage):
    def __init__(self, database: str = ":memory:", **kwargs: Any) -> None:  # noqa: ANN401
        self._database = database
        self._kwargs = kwargs
        self._db: aiosqlite.Connection | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self._database, **self._kwargs)
            await self._db.execute(
                "CREATE TABLE IF NOT EXISTS signal_client (key TEXT UNIQUE, value TEXT)"
            )
        return self._db

    async def exists(self, key: str) -> bool:
        db = await self._get_db()
        async with db.execute(
            "SELECT EXISTS(SELECT 1 FROM signal_client WHERE key = ?)",
            [key],
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] == 1 if result else False

    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        try:
            db = await self._get_db()
            async with db.execute(
                "SELECT value FROM signal_client WHERE key = ?",
                [key],
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return json.loads(result[0])
                msg = f"Key '{key}' not found in SQLite storage."
                raise StorageError(msg)
        except (aiosqlite.Error, TypeError, json.JSONDecodeError) as e:
            msg = f"SQLite load failed: {e}"
            raise StorageError(msg) from e

    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        try:
            db = await self._get_db()
            value = json.dumps(data)
            await db.execute(
                (
                    "INSERT INTO signal_client (key, value) VALUES (?, ?)"
                    " ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                ),
                [key, value],
            )
            await db.commit()
        except (aiosqlite.Error, TypeError) as e:
            msg = f"SQLite save failed: {e}"
            raise StorageError(msg) from e

    async def delete(self, key: str) -> None:
        try:
            db = await self._get_db()
            await db.execute("DELETE FROM signal_client WHERE key = ?", [key])
            await db.commit()
        except aiosqlite.Error as e:
            msg = f"SQLite delete failed: {e}"
            raise StorageError(msg) from e

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
