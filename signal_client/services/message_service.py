from __future__ import annotations

import asyncio
import json
from enum import Enum

import structlog

from ..domain.message import Message, MessageType
from ..infrastructure.websocket_client import WebSocketClient

log = structlog.get_logger()


class UnsupportedMessageError(Exception):
    """Custom exception for unsupported message types."""


class MessageService:
    def __init__(
        self, websocket_client: WebSocketClient, queue: asyncio.Queue[Message]
    ):
        self._websocket_client = websocket_client
        self._queue = queue

    async def listen(self):
        """Listen for incoming messages and process them."""
        async for raw_message in self._websocket_client.listen():
            try:
                message = self._parse_message(raw_message)
                if message:
                    await self._queue.put(message)
            except UnsupportedMessageError as e:
                log.debug("Ignoring unsupported message", error=e)
            except (json.JSONDecodeError, KeyError) as e:
                log.error("Failed to parse message", error=e, raw_message=raw_message)

    def _parse_message(self, raw_message_str: str) -> Message | None:
        """
        Parses a raw JSON string from the WebSocket into a domain.Message object.
        """
        raw_message = json.loads(raw_message_str)
        envelope = raw_message.get("envelope", {})

        if not envelope or "source" not in envelope:
            raise UnsupportedMessageError("Missing envelope or source")

        if "syncMessage" in envelope:
            data_message = envelope["syncMessage"].get("sentMessage", {})
            message_type = MessageType.SYNC_MESSAGE
        elif "dataMessage" in envelope:
            data_message = envelope["dataMessage"]
            message_type = MessageType.DATA_MESSAGE
        else:
            raise UnsupportedMessageError("Not a sync or data message")

        if not data_message:
            return None  # Ignore empty sync messages

        if "editMessage" in data_message:
            message_type = MessageType.EDIT_MESSAGE
            edit_info = data_message["editMessage"]
            data_message = edit_info.get("dataMessage", {})
            data_message["target_sent_timestamp"] = edit_info.get(
                "targetSentTimestamp"
            )

        if "remoteDelete" in data_message:
            message_type = MessageType.DELETE_MESSAGE
            delete_info = data_message["remoteDelete"]
            data_message["remote_delete_timestamp"] = delete_info.get("timestamp")

        # Common fields
        data_message["source"] = envelope.get("source")
        data_message["source_number"] = envelope.get("sourceNumber")
        data_message["source_uuid"] = envelope.get("sourceUuid")
        data_message["timestamp"] = envelope.get("timestamp")
        data_message["type"] = message_type

        # Extract nested structures
        if "groupInfo" in data_message:
            data_message["group"] = data_message["groupInfo"].get("groupId")

        if "reaction" in data_message:
            data_message["reaction_emoji"] = data_message["reaction"].get("emoji")
            data_message["reaction_target_author"] = data_message["reaction"].get(
                "targetAuthor"
            )
            data_message["reaction_target_timestamp"] = data_message["reaction"].get(
                "targetSentTimestamp"
            )

        if "attachments" in data_message:
            data_message["attachments_local_filenames"] = [
                attachment["filename"]
                for attachment in data_message["attachments"]
                if "filename" in attachment
            ]

        if "mentions" in data_message:
            data_message["mentions"] = [
                mention["number"]
                for mention in data_message["mentions"]
                if "number" in mention
            ]

        return Message.model_validate(data_message)