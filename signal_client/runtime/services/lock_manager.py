"""Manages asynchronous locks, supporting both local and distributed (Redis) locking."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog

log = structlog.get_logger()

if TYPE_CHECKING:
    import redis.asyncio as redis


class LockManager:
    """A manager for asyncio.Lock objects to prevent race conditions."""

    def __init__(
        self,
        *,
        redis_client: redis.Redis | None = None,
        lock_timeout_seconds: int = 30,
    ) -> None:
        """Initialize the LockManager.

        Args:
            redis_client: An optional Redis client for distributed locks.
            lock_timeout_seconds: Timeout for distributed locks in seconds.

        """
        self._locks: dict[str, asyncio.Lock] = {}
        self._manager_lock = asyncio.Lock()
        self._holders: dict[str, asyncio.Task] = {}
        self._redis_client = redis_client
        self._lock_timeout_seconds = lock_timeout_seconds

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

        if self._redis_client:
            redis_lock = self._redis_client.lock(
                resource_id, timeout=self._lock_timeout_seconds
            )
            acquired = await redis_lock.acquire(blocking=True)
            if not acquired:
                msg = f"Failed to acquire distributed lock for {resource_id}"
                raise RuntimeError(msg)
            try:
                self._holders[resource_id] = current_task
                yield
            finally:
                del self._holders[resource_id]
                try:
                    await redis_lock.release()
                except Exception:  # noqa: BLE001
                    log.warning(
                        "Failed to release distributed lock.",
                        resource_id=resource_id,
                    )
            return

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
