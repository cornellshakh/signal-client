from __future__ import annotations

import asyncio


class LockManager:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, lock_name: str) -> None:
        """Acquire a lock."""
        if lock_name not in self._locks:
            self._locks[lock_name] = asyncio.Lock()
        await self._locks[lock_name].acquire()

    def release(self, lock_name: str) -> None:
        """Release a lock."""
        if lock_name in self._locks:
            self._locks[lock_name].release()
