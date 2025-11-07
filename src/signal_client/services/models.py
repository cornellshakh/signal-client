from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QueuedMessage:
    raw: str
    enqueued_at: float


__all__ = ["QueuedMessage"]
