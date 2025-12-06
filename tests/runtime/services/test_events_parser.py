from __future__ import annotations

import json

import pytest

from signal_client.adapters.api.schemas.events import (
    BlockEvent,
    CallEvent,
    CallEventType,
    MessageEvent,
    ReceiptEvent,
    ReceiptType,
    TypingAction,
    TypingEvent,
    VerificationEvent,
)
from signal_client.runtime.services.message_parser import MessageParser

"""Tests for the event parser."""

TIMESTAMP = 1_700_000_000_000


@pytest.fixture
def parser() -> MessageParser:
    """Return a message parser."""
    return MessageParser()


def _wrap_envelope(payload: dict) -> str:
    return json.dumps({"envelope": payload})


def test_parse_event_message(parser: MessageParser) -> None:
    """Test parsing of a message event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "dataMessage": {"message": "event test"},
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, MessageEvent)
    assert event.message.message == "event test"
    assert event.envelope.timestamp == TIMESTAMP


def test_parse_event_receipt(parser: MessageParser) -> None:
    """Test parsing of a receipt event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "receiptMessage": {
                "when": TIMESTAMP - 10,
                "isDelivery": True,
                "timestamps": [TIMESTAMP - 10],
            },
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, ReceiptEvent)
    assert event.receipt_type is ReceiptType.DELIVERY
    assert event.timestamps == [TIMESTAMP - 10]
    assert event.when == TIMESTAMP - 10


def test_parse_event_typing(parser: MessageParser) -> None:
    """Test parsing of a typing event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "typingMessage": {
                "action": "started",
                "groupId": "group-1",
                "timestamp": TIMESTAMP,
            },
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, TypingEvent)
    assert event.action is TypingAction.STARTED
    assert event.group_id == "group-1"
    assert event.envelope.source == "+123"


def test_parse_event_call(parser: MessageParser) -> None:
    """Test parsing of a call event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "callMessage": {
                "offerMessage": {
                    "id": "offer-1",
                    "sdp": "sample",
                }
            },
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, CallEvent)
    assert event.call_type is CallEventType.OFFER
    assert event.offer == {"id": "offer-1", "sdp": "sample"}


def test_parse_event_verification(parser: MessageParser) -> None:
    """Test parsing of a verification event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "verification": {"state": "verified", "identityKey": "abc"},
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, VerificationEvent)
    assert event.state.value == "verified"
    assert event.identity_key == "abc"


def test_parse_event_block(parser: MessageParser) -> None:
    """Test parsing of a block event."""
    raw = _wrap_envelope(
        {
            "source": "+123",
            "timestamp": TIMESTAMP,
            "isBlocked": True,
        }
    )
    event = parser.parse_event(raw)
    assert isinstance(event, BlockEvent)
    assert event.blocked is True
