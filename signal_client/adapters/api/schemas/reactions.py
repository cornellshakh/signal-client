from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ReactionRequest(BaseModel):
    recipient: str
    reaction: str
    target_author: str
    timestamp: int

    model_config = ConfigDict(populate_by_name=True)
