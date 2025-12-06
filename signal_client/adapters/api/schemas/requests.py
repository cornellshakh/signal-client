from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .link_preview import LinkPreview


class MessageMention(BaseModel):
    author: str
    start: int
    length: int

    model_config = ConfigDict(populate_by_name=True)


class SendMessageRequest(BaseModel):
    message: str
    recipients: list[str] | None = None
    number: str | None = None
    base64_attachments: list[str] = Field(default_factory=list)
    mentions: list[MessageMention] | None = None
    quote_mentions: list[MessageMention] | None = None
    sticker: str | None = None
    notify_self: bool | None = None
    edit_timestamp: int | None = None
    view_once: bool = False
    quote_author: str | None = None
    quote_message: str | None = None
    quote_timestamp: int | None = None
    link_preview: LinkPreview | None = Field(default=None, alias="link_preview")
    text_mode: Literal["normal", "styled"] | None = None
    idempotency_key: str | None = Field(default=None, exclude=True)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TypingIndicatorRequest(BaseModel):
    recipient: str | None = None
    group: str | None = Field(default=None, exclude=True)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def populate_recipient(cls, values: dict[str, object]) -> dict[str, object]:
        recipient = values.get("recipient")
        if recipient:
            return values

        group = values.get("group")
        if group:
            values["recipient"] = group
        return values


class RemoteDeleteRequest(BaseModel):
    recipient: str
    timestamp: int
    idempotency_key: str | None = Field(default=None, exclude=True)


class AddStickerPackRequest(BaseModel):
    pack_id: str
    pack_key: str
