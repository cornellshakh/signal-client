from __future__ import annotations

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    message: str
    recipients: list[str]
    number: str
    base64_attachments: list[str] = Field(default_factory=list)
    mentions: list[dict] | None = None
    view_once: bool = False
    quote_author: str | None = None
    quote_message: str | None = None
    quote_timestamp: int | None = None


class TypingIndicatorRequest(BaseModel):
    group: str | None = None
    recipient: str | None = None
