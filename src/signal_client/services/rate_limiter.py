from __future__ import annotations

import asyncio
import time
from collections import deque

from signal_client.metrics import RATE_LIMITER_WAIT


class RateLimiter:
    """A rate limiter to avoid exceeding API limits."""

    def __init__(self, rate_limit: int, period: float) -> None:
        self.rate_limit = rate_limit
        self.period = period
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a permit from the rate limiter."""
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._timestamps and self._timestamps[0] <= now - self.period:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.rate_limit:
                    self._timestamps.append(now)
                    return

                sleep_time = self._timestamps[0] + self.period - now
                RATE_LIMITER_WAIT.observe(max(sleep_time, 0.0))
                await asyncio.sleep(sleep_time)
