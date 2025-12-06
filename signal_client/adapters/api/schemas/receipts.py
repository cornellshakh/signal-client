"""Pydantic models for receipt payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReceiptRequest(BaseModel):
    """Request body for sending read/viewed receipts."""

    recipient: str | None = None
    timestamp: int
    receipt_type: Literal["read", "viewed"] = Field(
        default="read", alias="receipt_type"
    )
    group: str | None = Field(default=None, exclude=True)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def populate_recipient(cls, values: dict[str, object]) -> dict[str, object]:
        """Populate recipient from group if provided."""
        recipient = values.get("recipient")
        if recipient:
            return values

        group = values.get("group")
        if isinstance(group, str) and group:
            values["recipient"] = group
        return values

    @model_validator(mode="after")
    def ensure_recipient(self) -> ReceiptRequest:
        """Ensure a recipient is present after validation."""
        if self.recipient:
            return self

        message = "recipient is required for receipts"
        raise ValueError(message)
