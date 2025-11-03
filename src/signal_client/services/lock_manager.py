from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog

log = structlog.get_logger()


class LockManager:
    """A manager for asyncio.Lock objects to prevent race conditions."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._manager_lock = asyncio.Lock()
        self._holders: dict[str, asyncio.Task] = {}

    @asynccontextmanager
    async def lock(self, resource_id: str) -> AsyncGenerator[None, None]:
        """Acquire a lock for a specific resource."""
        current_task = asyncio.current_task()
        if current_task is None:
            msg = "LockManager.lock() called outside of an asyncio task."
            raise RuntimeError(msg)

        if self._holders.get(resource_id) is current_task:
            log.warning(
                "Deadlock warning: Task is trying to acquire a lock it already holds.",
                resource_id=resource_id,
                task=current_task.get_name(),
            )

        async with self._manager_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = asyncio.Lock()

        resource_lock = self._locks[resource_id]
        async with resource_lock:
            self._holders[resource_id] = current_task
            try:
                yield
            finally:
                del self._holders[resource_id]
