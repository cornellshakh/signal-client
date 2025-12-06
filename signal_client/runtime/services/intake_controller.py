"""Manages message intake, handling pauses due to backpressure or circuit trips."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from signal_client.observability.metrics import INGEST_PAUSES

log = structlog.get_logger()


class IntakeController:
    """Coordinates ingest pauses under backpressure or circuit trips."""

    def __init__(self, default_pause_seconds: float = 1.0) -> None:
        """Initialize the IntakeController.

        Args:
            default_pause_seconds: Default duration to pause intake, in seconds.

        """
        self._default_pause_seconds = max(0.0, default_pause_seconds)
        self._pause_until = 0.0
        self._lock = asyncio.Lock()

    async def pause(self, *, reason: str, duration: float | None = None) -> None:
        """Pause message intake for a specified duration or default.

        Args:
            reason: The reason for pausing intake.
            duration: Optional duration to pause, in seconds. Uses default if None.

        """
        pause_seconds = (
            max(0.0, duration) if duration is not None else self._default_pause_seconds
        )
        pause_until = time.monotonic() + pause_seconds
        async with self._lock:
            self._pause_until = max(self._pause_until, pause_until)
        INGEST_PAUSES.labels(reason=reason).inc()
        log.warning(
            "ingest.paused",
            reason=reason,
            pause_seconds=pause_seconds,
            until=self._pause_until,
        )

    async def wait_if_paused(self) -> None:
        """Wait asynchronously if message intake is currently paused."""
        while True:
            async with self._lock:
                pause_remaining = self._pause_until - time.monotonic()
            if pause_remaining <= 0:
                return
            await asyncio.sleep(min(pause_remaining, 1.0))

    async def resume_now(self) -> None:
        """Immediately resume message intake, ending any current pause."""
        async with self._lock:
            self._pause_until = 0.0
        log.info("ingest.resumed")

    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot of the current intake controller state."""
        return {
            "paused_until": self._pause_until,
            "default_pause_seconds": self._default_pause_seconds,
        }


__all__ = ["IntakeController"]
