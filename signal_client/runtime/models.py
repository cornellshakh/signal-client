"""Runtime data structures for queued websocket messages."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING


@dataclass(slots=True)
class QueuedMessage:
    """Queued message ready for worker processing."""

    raw: str
    enqueued_at: float
    recipient: str | None = None
    message: Message | None = None
    ack: Callable[[], None] | None = None


__all__ = ["QueuedMessage"]

if TYPE_CHECKING:  # pragma: no cover - circular import guard
    from signal_client.adapters.api.schemas.message import Message
