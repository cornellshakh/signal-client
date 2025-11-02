from enum import Enum

from pydantic import BaseModel


class MessageType(Enum):
    DATA_MESSAGE = "DATA_MESSAGE"
    SYNC_MESSAGE = "SYNC_MESSAGE"
    EDIT_MESSAGE = "EDIT_MESSAGE"
    DELETE_MESSAGE = "DELETE_MESSAGE"


class Message(BaseModel):
    message: str | None = None
    source: str
    timestamp: int
    type: MessageType
    group: dict | None = None
    reaction_emoji: str | None = None
    target_sent_timestamp: int | None = None
    remote_delete_timestamp: int | None = None
    reaction_target_author: str | None = None
    reaction_target_timestamp: int | None = None
    attachments_local_filenames: list[str] | None = None
    mentions: list[str] | None = None

    def recipient(self) -> str:
        if self.is_group() and self.group:
            return self.group["groupId"]
        return self.source

    def is_group(self) -> bool:
        return self.group is not None

    def is_private(self) -> bool:
        return not self.is_group()
