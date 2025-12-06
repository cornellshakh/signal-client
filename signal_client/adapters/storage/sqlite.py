"""SQLite storage implementation for the Signal client."""

import json
from typing import Any

import aiosqlite

from .base import Storage, StorageError


class SQLiteStorage(Storage):
    """SQLite-backed storage implementation."""

    def __init__(self, database: str = ":memory:", **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the SQLiteStorage.

        Args:
            database: The path to the SQLite database file.
                Defaults to an in-memory database.
            **kwargs: Additional keyword arguments for `aiosqlite.connect`.

        """
        self._database = database
        self._kwargs: dict[str, Any] = dict(kwargs)
        self._db: aiosqlite.Connection | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self._database, **self._kwargs)
            await self._db.execute(
                "CREATE TABLE IF NOT EXISTS signal_client_dlq (key TEXT, value TEXT)"
            )
        return self._db

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()

    async def append(self, key: str, data: dict[str, Any]) -> None:
        """Append data to a list associated with a key."""
        try:
            db = await self._get_db()
            value = json.dumps(data)
            await db.execute(
                "INSERT INTO signal_client_dlq (key, value) VALUES (?, ?)",
                [key, value],
            )
            await db.commit()
        except (aiosqlite.Error, TypeError) as e:
            msg = f"SQLite append failed: {e}"
            raise StorageError(msg) from e

    async def read_all(self, key: str) -> list[dict[str, Any]]:
        """Read all data associated with a key."""
        try:
            db = await self._get_db()
            async with db.execute(
                "SELECT value FROM signal_client_dlq WHERE key = ? ORDER BY rowid ASC",
                [key],
            ) as cursor:
                results = await cursor.fetchall()
                return [json.loads(row[0]) for row in results]
        except (aiosqlite.Error, TypeError, json.JSONDecodeError) as e:
            msg = f"SQLite read_all failed: {e}"
            raise StorageError(msg) from e

    async def delete_all(self, key: str) -> None:
        """Delete all data associated with a key."""
        try:
            db = await self._get_db()
            await db.execute("DELETE FROM signal_client_dlq WHERE key = ?", [key])
            await db.commit()
        except aiosqlite.Error as e:
            msg = f"SQLite delete_all failed: {e}"
            raise StorageError(msg) from e
