import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageType(Enum):
    DATA_MESSAGE = "DATA_MESSAGE"
    SYNC_MESSAGE = "SYNC_MESSAGE"
    EDIT_MESSAGE = "EDIT_MESSAGE"
    DELETE_MESSAGE = "DELETE_MESSAGE"


class AttachmentPointer(BaseModel):
    id: str
    content_type: str | None = Field(default=None, alias="contentType")
    filename: str | None = None
    size: int | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("size", mode="before")
    @classmethod
    def normalize_size(cls, value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None


class Message(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    message: str | None = None
    source: str
    timestamp: int
    type: MessageType
    group: dict | None = Field(default=None, alias="groupInfo")
    reaction_emoji: str | None = None
    target_sent_timestamp: int | None = None
    remote_delete_timestamp: int | None = None
    reaction_target_author: str | None = None
    reaction_target_timestamp: int | None = None
    attachments_local_filenames: list[str] | None = None
    attachments: list[AttachmentPointer] | None = None
    mentions: list[str] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("attachments_local_filenames", mode="before")
    @classmethod
    def clean_attachments(cls, v: object) -> object:
        if isinstance(v, list):
            return [i for i in v if isinstance(i, str)]
        return v

    def recipient(self) -> str:
        if self.is_group() and self.group:
            return self.group["groupId"]
        return self.source

    def is_group(self) -> bool:
        return self.group is not None

    def is_private(self) -> bool:
        return not self.is_group()
