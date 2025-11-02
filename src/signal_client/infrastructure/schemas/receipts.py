from __future__ import annotations

from pydantic import BaseModel


class ReceiptRequest(BaseModel):
    recipient: str | None = None
    group: str | None = None
    target_timestamp: int
    type: str = "read"
