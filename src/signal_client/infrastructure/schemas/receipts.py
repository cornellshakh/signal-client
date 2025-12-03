from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ReceiptRequest(BaseModel):
    recipient: str | None = None
    group: str | None = None
    timestamp: int
    receipt_type: str = Field(default="read", alias="receipt_type")

    model_config = ConfigDict(populate_by_name=True)
