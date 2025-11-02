import json
from typing import Any

import aiosqlite

from .base import Storage, StorageError


class SQLiteStorage(Storage):
    def __init__(self, database: str = ":memory:", **kwargs):
        self._database = database
        self._kwargs = kwargs
        self._db = None

    async def _get_db(self):
        if self._db is None:
            self._db = await aiosqlite.connect(self._database, **self._kwargs)
            await self._db.execute(
                "CREATE TABLE IF NOT EXISTS signal_client (key text unique, value text)",
            )
        return self._db

    async def exists(self, key: str) -> bool:
        db = await self._get_db()
        async with db.execute(
            "SELECT EXISTS(SELECT 1 FROM signal_client WHERE key = ?)",
            [key],
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else False

    async def read(self, key: str) -> Any:
        try:
            db = await self._get_db()
            async with db.execute(
                "SELECT value FROM signal_client WHERE key = ?",
                [key],
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return json.loads(result[0])
                raise StorageError(f"Key '{key}' not found in SQLite storage.")
        except Exception as e:
            raise StorageError(f"SQLite load failed: {e}")

    async def save(self, key: str, object: Any) -> None:
        try:
            db = await self._get_db()
            value = json.dumps(object)
            await db.execute(
                "INSERT INTO signal_client VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",
                [key, value, value],
            )
            await db.commit()
        except Exception as e:
            raise StorageError(f"SQLite save failed: {e}")

    async def delete(self, key: str) -> None:
        try:
            db = await self._get_db()
            await db.execute("DELETE FROM signal_client WHERE key = ?", [key])
            await db.commit()
        except Exception as e:
            raise StorageError(f"SQLite delete failed: {e}")