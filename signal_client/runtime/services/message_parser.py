"""Parsers for incoming websocket messages."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from pydantic import ValidationError

from signal_client.adapters.api.schemas.events import (
    BaseEvent,
    BlockEvent,
    CallEvent,
    EnvelopeMetadata,
    MessageEvent,
    ReceiptEvent,
    TypingEvent,
    VerificationEvent,
)
from signal_client.adapters.api.schemas.message import Message, MessageType

log = logging.getLogger(__name__)


class MessageParser:
    """Parses raw websocket messages into structured event or message objects."""

    def parse_event(self, raw_message_str: str) -> BaseEvent | None:
        """Parse raw JSON into a typed event when possible."""
        raw_message = self._load_message(raw_message_str)
        if raw_message is None:
            return None

        envelope = raw_message.get("envelope", {})
        if not self._is_valid_envelope(envelope):
            return None

        metadata = self._metadata(envelope)
        try:
            event = self._extract_event(envelope, metadata)
        except ValidationError as exc:
            log.warning(
                "message_parser.event_validation_failed",
                errors=exc.errors(include_input=False),
            )
            return None
        return event

    def parse(self, raw_message_str: str) -> Message | None:
        """Parse raw JSON into a Message instance when possible."""
        event = self.parse_event(raw_message_str)
        if isinstance(event, MessageEvent):
            return event.message
        return None

    def recipient_from_raw(self, raw_message_str: str) -> str | None:  # noqa: PLR0911
        """Best-effort extraction of a conversation recipient for sharding."""
        raw_message = self._load_message(raw_message_str)
        if raw_message is None:
            return None

        envelope = raw_message.get("envelope", {})
        if not self._is_valid_envelope(envelope):
            return None

        try:
            event = self._extract_event(envelope, self._metadata(envelope))
        except ValidationError:
            return self._extract_source(envelope)
        if isinstance(event, MessageEvent):
            group_id = self._extract_group(event.message)
            if group_id:
                return group_id
            return event.message.recipient()

        if isinstance(event, TypingEvent):
            return event.group_id or event.envelope.source
        if isinstance(event, ReceiptEvent):
            return self._extract_group_from_envelope(envelope) or event.envelope.source
        return self._extract_source(envelope)

    def _load_message(self, raw_message_str: str) -> dict[str, Any] | None:
        try:
            return json.loads(raw_message_str)
        except json.JSONDecodeError as exc:
            try:
                log.warning("message_parser.json_decode_failed", error=str(exc))
            except TypeError:
                log.warning("message_parser.json_decode_failed: %s", str(exc))
            return None

    @staticmethod
    def _is_valid_envelope(envelope: dict[str, Any]) -> bool:
        return bool(envelope) and "source" in envelope

    def _metadata(self, envelope: dict[str, Any]) -> EnvelopeMetadata:
        metadata_payload = {
            "source": envelope.get("source"),
            "sourceNumber": envelope.get("sourceNumber"),
            "sourceUuid": envelope.get("sourceUuid"),
            "sourceDevice": envelope.get("sourceDevice"),
            "relay": envelope.get("relay"),
            "timestamp": envelope.get("timestamp"),
        }
        return EnvelopeMetadata.model_validate(metadata_payload)

    def _extract_event(  # noqa: C901, PLR0911
        self, envelope: dict[str, Any], metadata: EnvelopeMetadata
    ) -> BaseEvent | None:
        if "syncMessage" in envelope or "dataMessage" in envelope:
            data_message, message_type = self._extract_message(envelope)
            if data_message is None:
                return None
            self._apply_common_metadata(data_message, envelope, message_type)
            self._apply_reaction_metadata(data_message)
            self._apply_attachment_metadata(data_message)
            self._apply_mentions(data_message)
            self._sanitize_identifier(data_message)
            message = Message.model_validate(data_message)
            return MessageEvent(envelope=metadata, message=message)

        if "receiptMessage" in envelope:
            payload = envelope.get("receiptMessage")
            if isinstance(payload, dict):
                return ReceiptEvent.model_validate({"envelope": metadata, **payload})

        if "typingMessage" in envelope:
            payload = envelope.get("typingMessage")
            if isinstance(payload, dict):
                return TypingEvent.model_validate({"envelope": metadata, **payload})

        if "callMessage" in envelope:
            payload = envelope.get("callMessage")
            if isinstance(payload, dict):
                return CallEvent.model_validate({"envelope": metadata, **payload})

        verification = envelope.get("verification") or envelope.get("verified")
        if isinstance(verification, dict):
            return VerificationEvent.model_validate(
                {"envelope": metadata, **verification}
            )
        if isinstance(verification, bool):
            return VerificationEvent(envelope=metadata, verified=verification)

        if "isBlocked" in envelope or "blocked" in envelope:
            return BlockEvent(
                envelope=metadata,
                blocked=bool(envelope.get("isBlocked") or envelope.get("blocked")),
            )
        return None

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
            filenames: list[str] = []
            normalized: list[dict[str, object]] = []
            for attachment in attachments:
                if not isinstance(attachment, dict):
                    continue
                filename = attachment.get("filename")
                attachment_id = attachment.get("id")
                if isinstance(filename, str):
                    filenames.append(filename)
                if isinstance(attachment_id, str):
                    normalized.append(
                        {
                            "id": attachment_id,
                            "content_type": attachment.get("contentType")
                            or attachment.get("content_type"),
                            "filename": filename if isinstance(filename, str) else None,
                            "size": attachment.get("size"),
                        }
                    )
            if filenames:
                data_message["attachments_local_filenames"] = filenames
            if normalized:
                data_message["attachments"] = normalized

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

    @staticmethod
    def _extract_source(envelope: dict[str, Any]) -> str | None:
        source = envelope.get("source")
        return source if isinstance(source, str) and source else None

    @staticmethod
    def _extract_group(message: Message) -> str | None:
        group = message.group
        if isinstance(group, dict):
            group_id = group.get("groupId")
            if isinstance(group_id, str) and group_id:
                return group_id
        return None

    @staticmethod
    def _extract_group_from_envelope(envelope: dict[str, Any]) -> str | None:
        group_info = envelope.get("groupInfo") or envelope.get("group")
        if isinstance(group_info, dict):
            group_id = group_info.get("groupId")
            if isinstance(group_id, str) and group_id:
                return group_id
        return None
