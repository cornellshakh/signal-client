from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from signal_client.infrastructure.storage.base import Storage


class DeadLetterQueue:
    def __init__(self, storage: Storage, queue_name: str) -> None:
        self._storage = storage
        self._queue_name = queue_name

    async def send(self, message: dict[str, Any]) -> None:
        await self._storage.append(self._queue_name, message)

    async def replay(self) -> list[dict[str, Any]]:
        messages = await self._storage.read_all(self._queue_name)
        await self._storage.delete_all(self._queue_name)
        return messages
