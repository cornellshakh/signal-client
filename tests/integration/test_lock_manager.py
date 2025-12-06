"""Integration tests for the LockManager."""

from __future__ import annotations

import asyncio

import pytest

from signal_client.runtime.services.lock_manager import LockManager


@pytest.mark.asyncio
async def test_lock_manager_serializes_access():
    """Test that the LockManager serializes access to a resource."""
    manager = LockManager()
    events: list[str] = []

    async def task(name: str) -> None:
        async with manager.lock("resource"):
            events.append(f"acquired-{name}")
            await asyncio.sleep(0.01)
            events.append(f"released-{name}")

    await asyncio.gather(task("one"), task("two"))

    assert events[0] == "acquired-one"
    assert events[1] == "released-one"
    assert events[2] == "acquired-two"
    assert events[3] == "released-two"
