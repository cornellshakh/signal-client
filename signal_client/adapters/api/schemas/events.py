from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .message import Message


class EventType(str, Enum):
    MESSAGE = "message"
    RECEIPT = "receipt"
    TYPING = "typing"
    CALL = "call"
    VERIFICATION = "verification"
    BLOCK = "block"


class EnvelopeMetadata(BaseModel):
    source: str | None = None
    source_number: str | None = Field(default=None, alias="sourceNumber")
    source_uuid: str | None = Field(default=None, alias="sourceUuid")
    source_device: int | None = Field(default=None, alias="sourceDevice")
    relay: str | None = None
    timestamp: int | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class BaseEvent(BaseModel):
    """Base envelope event."""

    type: EventType
    envelope: EnvelopeMetadata

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class MessageEvent(BaseEvent):
    type: EventType = Field(default=EventType.MESSAGE, frozen=True)
    message: Message


class ReceiptType(str, Enum):
    DELIVERY = "delivery"
    READ = "read"
    VIEWED = "viewed"
    UNKNOWN = "unknown"


class ReceiptEvent(BaseEvent):
    type: EventType = Field(default=EventType.RECEIPT, frozen=True)
    receipt_type: ReceiptType = ReceiptType.UNKNOWN
    timestamps: list[int] = Field(default_factory=list)
    when: int | None = None
    is_delivery: bool = Field(default=False, alias="isDelivery")
    is_read: bool = Field(default=False, alias="isRead")
    is_viewed: bool = Field(default=False, alias="isViewed")
    is_unidentified_sender: bool | None = Field(
        default=None, alias="isUnidentifiedSender"
    )

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @field_validator("timestamps", mode="before")
    @classmethod
    def normalize_timestamps(cls, value: object) -> list[int]:
        if value is None:
            return []
        if isinstance(value, list):
            return [ts for ts in value if isinstance(ts, int)]
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            try:
                parsed = int(value)
            except ValueError:
                return []
            return [parsed]
        return []

    @model_validator(mode="before")
    @classmethod
    def derive_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        when = values.get("when")
        timestamps = values.get("timestamps")
        if when is None and isinstance(timestamps, list) and timestamps:
            values["when"] = timestamps[0]
        elif isinstance(when, int) and not timestamps:
            values["timestamps"] = [when]

        receipt_type = values.get("receipt_type") or values.get("type")
        normalized = cls._normalize_receipt_type(
            receipt_type,
            is_read=values.get("isRead") or values.get("is_read"),
            is_viewed=values.get("isViewed") or values.get("is_viewed"),
            is_delivery=values.get("isDelivery") or values.get("is_delivery"),
        )
        values["receipt_type"] = normalized
        return values

    @staticmethod
    def _normalize_receipt_type(  # noqa: PLR0911
        receipt_type: object,
        *,
        is_read: object,
        is_viewed: object,
        is_delivery: object,
    ) -> ReceiptType:
        if isinstance(receipt_type, ReceiptType):
            return receipt_type
        if isinstance(receipt_type, str):
            lowered = receipt_type.strip().lower()
            if lowered in {"delivery", "delivered"}:
                return ReceiptType.DELIVERY
            if lowered in {"read", "opened"}:
                return ReceiptType.READ
            if lowered in {"viewed", "seen"}:
                return ReceiptType.VIEWED
        if is_viewed:
            return ReceiptType.VIEWED
        if is_read:
            return ReceiptType.READ
        if is_delivery:
            return ReceiptType.DELIVERY
        return ReceiptType.UNKNOWN


class TypingAction(str, Enum):
    STARTED = "started"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class TypingEvent(BaseEvent):
    type: EventType = Field(default=EventType.TYPING, frozen=True)
    action: TypingAction = TypingAction.UNKNOWN
    timestamp: int | None = None
    group_id: str | None = Field(default=None, alias="groupId")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: object) -> TypingAction:
        if isinstance(value, TypingAction):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"started", "start"}:
                return TypingAction.STARTED
            if lowered in {"stopped", "stop"}:
                return TypingAction.STOPPED
        return TypingAction.UNKNOWN


class CallEventType(str, Enum):
    OFFER = "offer"
    ANSWER = "answer"
    HANGUP = "hangup"
    BUSY = "busy"
    ICE_UPDATE = "ice_update"
    UNKNOWN = "unknown"


class CallEvent(BaseEvent):
    type: EventType = Field(default=EventType.CALL, frozen=True)
    call_type: CallEventType = CallEventType.UNKNOWN
    offer: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None
    hangup: dict[str, Any] | None = None
    busy: dict[str, Any] | None = None
    ice_updates: list[dict[str, Any]] | None = Field(default=None, alias="iceUpdates")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def determine_call_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "call_type" in values and isinstance(values["call_type"], CallEventType):
            return values

        for key, event_type in (
            ("offerMessage", CallEventType.OFFER),
            ("answerMessage", CallEventType.ANSWER),
            ("hangupMessage", CallEventType.HANGUP),
            ("busyMessage", CallEventType.BUSY),
            ("iceUpdate", CallEventType.ICE_UPDATE),
        ):
            if key in values:
                values.setdefault("call_type", event_type)
                if key == "iceUpdate":
                    values["ice_updates"] = values.get("iceUpdate")
                elif key == "offerMessage":
                    values["offer"] = values.get(key)
                elif key == "answerMessage":
                    values["answer"] = values.get(key)
                elif key == "hangupMessage":
                    values["hangup"] = values.get(key)
                elif key == "busyMessage":
                    values["busy"] = values.get(key)
                break
        if "call_type" not in values:
            values["call_type"] = CallEventType.UNKNOWN
        return values


class VerificationState(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DEFAULT = "default"
    UNKNOWN = "unknown"


class VerificationEvent(BaseEvent):
    type: EventType = Field(default=EventType.VERIFICATION, frozen=True)
    verified: bool | None = None
    state: VerificationState = VerificationState.UNKNOWN
    identity_key: str | None = Field(default=None, alias="identityKey")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @model_validator(mode="before")
    @classmethod
    def normalize_state(cls, values: dict[str, Any]) -> dict[str, Any]:
        state = values.get("state")
        verified = values.get("verified")
        if isinstance(state, VerificationState):
            return values

        if isinstance(state, str):
            lowered = state.strip().lower()
            for option in VerificationState:
                if lowered == option.value:
                    values["state"] = option
                    return values
        if verified is True:
            values["state"] = VerificationState.VERIFIED
        elif verified is False:
            values["state"] = VerificationState.UNVERIFIED
        else:
            values["state"] = VerificationState.UNKNOWN
        return values


class BlockEvent(BaseEvent):
    type: EventType = Field(default=EventType.BLOCK, frozen=True)
    blocked: bool = False

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @field_validator("blocked", mode="before")
    @classmethod
    def normalize_blocked(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return False


__all__ = [
    "BaseEvent",
    "BlockEvent",
    "CallEvent",
    "CallEventType",
    "EnvelopeMetadata",
    "EventType",
    "MessageEvent",
    "ReceiptEvent",
    "ReceiptType",
    "TypingAction",
    "TypingEvent",
    "VerificationEvent",
    "VerificationState",
]
