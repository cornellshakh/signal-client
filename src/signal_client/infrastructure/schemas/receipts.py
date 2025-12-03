from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReceiptRequest(BaseModel):
    recipient: str | None = None
    timestamp: int
    receipt_type: Literal["read", "viewed"] = Field(default="read", alias="receipt_type")
    group: str | None = Field(default=None, exclude=True)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("recipient")
    @classmethod
    def ensure_recipient(cls, recipient: str | None, values: dict[str, object]) -> str:
        if recipient:
            return recipient

        group = values.get("group")
        if isinstance(group, str) and group:
            return group

        message = "recipient is required for receipts"
        raise ValueError(message)
