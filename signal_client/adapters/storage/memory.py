"""In-memory storage implementation for the Signal client."""

from collections import defaultdict
from typing import Any

from .base import Storage


class MemoryStorage(Storage):
    """A non-persistent, in-memory storage backend."""

    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._store: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)

    async def close(self) -> None:
        """Clears the in-memory store."""
        self._store.clear()

    async def append(self, key: str, data: dict[str, Any]) -> None:
        """Appends data to a key's list."""
        self._store[key].append(data)

    async def read_all(self, key: str) -> list[dict[str, Any]]:
        """Reads all data for a key."""
        return self._store.get(key, [])

    async def delete_all(self, key: str) -> None:
        """Deletes all data for a key."""
        if key in self._store:
            del self._store[key]
