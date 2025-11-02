from __future__ import annotations

from pydantic import BaseModel


class Reaction(BaseModel):
    emoji: str
    target_author_uuid: str
    target_timestamp: int
    author_uuid: str
    timestamp: int
