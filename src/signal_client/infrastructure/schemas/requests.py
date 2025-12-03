from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .link_preview import LinkPreview


class MessageMention(BaseModel):
    author: str
    start: int
    length: int

    model_config = ConfigDict(populate_by_name=True)


class SendMessageRequest(BaseModel):
    message: str
    recipients: list[str]
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
    text_mode: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TypingIndicatorRequest(BaseModel):
    group: str | None = None
    recipient: str | None = None


class RemoteDeleteRequest(BaseModel):
    recipient: str
    timestamp: int


class AddStickerPackRequest(BaseModel):
    pack_id: str
    pack_key: str
