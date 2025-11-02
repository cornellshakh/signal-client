from __future__ import annotations

from pydantic import BaseModel


class ReactionRequest(BaseModel):
    recipient: str | None = None
    group: str | None = None
    emoji: str
    target_author: str
    target_timestamp: int
