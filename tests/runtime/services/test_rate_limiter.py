"""Tests for the rate limiter service."""

from __future__ import annotations

import pytest

from signal_client.observability.metrics import RATE_LIMITER_WAIT
from signal_client.runtime.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_records_wait(monkeypatch):
    """Test that the rate limiter records wait times."""
    limiter = RateLimiter(rate_limit=1, period=0.5)
    await limiter.acquire()

    recorded: list[float] = []

    async def fake_sleep(duration: float) -> None:
        recorded.append(duration)

    monkeypatch.setattr(
        "signal_client.runtime.services.rate_limiter.asyncio.sleep", fake_sleep
    )

    await limiter.acquire()

    assert recorded
    assert RATE_LIMITER_WAIT._sum.get() >= recorded[0]  # type: ignore[attr-defined]
