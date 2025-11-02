from __future__ import annotations

import json

from signal_client.infrastructure.schemas.message import Message, MessageType
from signal_client.services.message_service import UnsupportedMessageError


class MessageParser:
    def parse(self, raw_message_str: str) -> Message | None:  # noqa: C901
        """
        Parses a raw JSON string from the WebSocket into a domain.Message object.
        """
        raw_message = json.loads(raw_message_str)
        envelope = raw_message.get("envelope", {})

        if not envelope or "source" not in envelope:
            msg = "Missing envelope or source"
            raise UnsupportedMessageError(msg)

        if "syncMessage" in envelope:
            data_message = envelope["syncMessage"].get("sentMessage", {})
            message_type = MessageType.SYNC_MESSAGE
        elif "dataMessage" in envelope:
            data_message = envelope["dataMessage"]
            message_type = MessageType.DATA_MESSAGE
        else:
            msg = "Not a sync or data message"
            raise UnsupportedMessageError(msg)

        if not data_message:
            return None  # Ignore empty sync messages

        if "editMessage" in data_message:
            message_type = MessageType.EDIT_MESSAGE
            edit_info = data_message["editMessage"]
            data_message = edit_info.get("dataMessage", {})
            data_message["target_sent_timestamp"] = edit_info.get("targetSentTimestamp")

        if "remoteDelete" in data_message:
            message_type = MessageType.DELETE_MESSAGE
            delete_info = data_message["remoteDelete"]
            data_message["remote_delete_timestamp"] = delete_info.get("timestamp")

        # Common fields
        data_message["source"] = envelope.get("source")
        data_message["source_number"] = envelope.get("sourceNumber")
        data_message["source_uuid"] = envelope.get("sourceUuid")
        data_message["timestamp"] = envelope.get("timestamp")
        data_message["type"] = message_type.value

        # Extract nested structures
        if "groupInfo" in data_message:
            data_message["group"] = data_message["groupInfo"]

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
