from __future__ import annotations

import json
import uuid
from typing import Any

import structlog
from pydantic import ValidationError

from signal_client.infrastructure.schemas.message import Message, MessageType

log = structlog.get_logger()


class MessageParser:
    def parse(self, raw_message_str: str) -> Message | None:
        """Parse raw JSON into a Message instance when possible."""
        raw_message = self._load_message(raw_message_str)
        if raw_message is None:
            return None

        envelope = raw_message.get("envelope", {})
        if not self._is_valid_envelope(envelope):
            return None

        data_message, message_type = self._extract_message(envelope)
        if data_message is None:
            return None

        self._apply_common_metadata(data_message, envelope, message_type)
        self._apply_reaction_metadata(data_message)
        self._apply_attachment_metadata(data_message)
        self._apply_mentions(data_message)
        self._sanitize_identifier(data_message)

        try:
            return Message.model_validate(data_message)
        except ValidationError as exc:
            log.warning(
                "message_parser.validation_failed",
                errors=exc.errors(include_input=False),
                message_type=message_type.value,
            )
            return None

    def _load_message(self, raw_message_str: str) -> dict[str, Any] | None:
        try:
            return json.loads(raw_message_str)
        except json.JSONDecodeError as exc:
            log.warning("message_parser.json_decode_failed", error=str(exc))
            return None

    @staticmethod
    def _is_valid_envelope(envelope: dict[str, Any]) -> bool:
        return bool(envelope) and "source" in envelope

    def _extract_message(
        self, envelope: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, MessageType]:
        message: dict[str, Any] | None
        if "syncMessage" in envelope:
            sent_message = envelope["syncMessage"].get("sentMessage")
            message = dict(sent_message) if isinstance(sent_message, dict) else {}
            message_type = MessageType.SYNC_MESSAGE
        elif "dataMessage" in envelope:
            data_payload = envelope.get("dataMessage")
            message = dict(data_payload) if isinstance(data_payload, dict) else {}
            message_type = MessageType.DATA_MESSAGE
        else:
            return None, MessageType.DATA_MESSAGE

        if not message:
            return None, message_type

        message_type = self._apply_special_cases(message, message_type)
        return message, message_type

    @staticmethod
    def _apply_special_cases(
        data_message: dict[str, Any],
        message_type: MessageType,
    ) -> MessageType:
        if "editMessage" in data_message:
            edit_info = data_message["editMessage"]
            replacement = edit_info.get("dataMessage", {})
            replacement["target_sent_timestamp"] = edit_info.get("targetSentTimestamp")
            data_message.clear()
            data_message.update(replacement)
            return MessageType.EDIT_MESSAGE

        if "remoteDelete" in data_message:
            delete_info = data_message["remoteDelete"]
            data_message["remote_delete_timestamp"] = delete_info.get("timestamp")
            return MessageType.DELETE_MESSAGE

        return message_type

    @staticmethod
    def _apply_common_metadata(
        data_message: dict[str, Any],
        envelope: dict[str, Any],
        message_type: MessageType,
    ) -> None:
        data_message["source"] = envelope.get("source")
        data_message["source_number"] = envelope.get("sourceNumber")
        data_message["source_uuid"] = envelope.get("sourceUuid")
        data_message["timestamp"] = envelope.get("timestamp")
        data_message["type"] = message_type.value

        if "groupInfo" in data_message:
            data_message["group"] = data_message["groupInfo"]

    @staticmethod
    def _apply_reaction_metadata(data_message: dict[str, Any]) -> None:
        reaction = data_message.get("reaction")
        if isinstance(reaction, dict):
            data_message["reaction_emoji"] = reaction.get("emoji")
            data_message["reaction_target_author"] = reaction.get("targetAuthor")
            data_message["reaction_target_timestamp"] = reaction.get(
                "targetSentTimestamp"
            )

    @staticmethod
    def _apply_attachment_metadata(data_message: dict[str, Any]) -> None:
        attachments = data_message.get("attachments")
        if isinstance(attachments, list):
            filenames = [
                attachment["filename"]
                for attachment in attachments
                if isinstance(attachment, dict) and "filename" in attachment
            ]
            data_message["attachments_local_filenames"] = filenames

    @staticmethod
    def _apply_mentions(data_message: dict[str, Any]) -> None:
        mentions = data_message.get("mentions")
        if isinstance(mentions, list):
            data_message["mentions"] = [
                mention["number"]
                for mention in mentions
                if isinstance(mention, dict) and "number" in mention
            ]

    @staticmethod
    def _sanitize_identifier(data_message: dict[str, Any]) -> None:
        message_id = data_message.get("id")
        if message_id is None:
            return
        if isinstance(message_id, (str, uuid.UUID)):
            return
        data_message.pop("id", None)
