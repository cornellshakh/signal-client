from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from signal_client.infrastructure.schemas.message import Message, MessageType
from signal_client.services.message_parser import MessageParser
from signal_client.services.worker_pool_manager import Worker, WorkerConfig

if TYPE_CHECKING:
    from signal_client.bot import SignalClient

TIMESTAMP = 1_672_531_200_000


@pytest.fixture
def message_parser() -> MessageParser:
    """Return a message parser."""
    return MessageParser()


@pytest.fixture
def worker(bot: SignalClient, message_parser: MessageParser) -> Worker:
    """Return a worker with mocked dependencies."""
    config = WorkerConfig(
        context_factory=bot.app.context_factory,
        queue=AsyncMock(),
        commands={},
        message_parser=message_parser,
        sensitive_trigger_regex=None,
        insensitive_trigger_regex=None,
        sensitive_triggers=[],
        insensitive_triggers=[],
        regex_commands=[],
        middleware=[],
    )
    return Worker(config)


def test_parse_message_simple_text(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "sourceNumber": "+1234567890",
            "sourceUuid": "some-uuid",
            "sourceName": "Test User",
            "sourceDevice": 1,
            "timestamp": TIMESTAMP,
            "dataMessage": {
                "timestamp": TIMESTAMP,
                "message": "Hello, world!",
                "expiresInSeconds": 0,
                "viewOnce": False,
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert isinstance(message, Message)
    assert message.message == "Hello, world!"
    assert message.source == "+1234567890"
    assert message.timestamp == TIMESTAMP


def test_parse_message_sync_message(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "sourceNumber": "+1234567890",
            "sourceUuid": "some-uuid",
            "sourceName": "Test User",
            "sourceDevice": 1,
            "timestamp": TIMESTAMP,
            "syncMessage": {
                "sentMessage": {
                    "timestamp": TIMESTAMP,
                    "message": "Hello from another device",
                    "expiresInSeconds": 0,
                    "viewOnce": False,
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.message == "Hello from another device"
    assert message.type == MessageType.SYNC_MESSAGE


def test_parse_message_edit_message(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531201000,
            "dataMessage": {
                "editMessage": {
                    "targetSentTimestamp": TIMESTAMP,
                    "dataMessage": {"message": "Hello, edited world!"},
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.message == "Hello, edited world!"
    assert message.type == MessageType.EDIT_MESSAGE
    assert message.target_sent_timestamp == TIMESTAMP


def test_parse_message_remote_delete(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531202000,
            "dataMessage": {"remoteDelete": {"timestamp": TIMESTAMP}},
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.type == MessageType.DELETE_MESSAGE
    assert message.remote_delete_timestamp == TIMESTAMP


def test_parse_message_reaction(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531203000,
            "dataMessage": {
                "reaction": {
                    "emoji": "👍",
                    "targetAuthor": "+0987654321",
                    "targetSentTimestamp": TIMESTAMP,
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.reaction_emoji == "👍"
    assert message.reaction_target_author == "+0987654321"
    assert message.reaction_target_timestamp == TIMESTAMP


def test_parse_message_group_message(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531204000,
            "dataMessage": {
                "message": "Hello, group!",
                "groupInfo": {"groupId": "some-group-id"},
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.message == "Hello, group!"
    assert message.group == {"groupId": "some-group-id"}
    assert message.is_group() is True
    assert message.is_private() is False


def test_parse_message_attachment(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531205000,
            "dataMessage": {
                "message": "Hello, attachment!",
                "attachments": [{"filename": "test.txt"}],
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.attachments_local_filenames == ["test.txt"]


def test_parse_message_mention(message_parser: MessageParser) -> None:
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531206000,
            "dataMessage": {
                "message": "Hello, @+0987654321!",
                "mentions": [{"number": "+0987654321"}],
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_parser.parse(raw_message_str)

    assert message is not None
    assert message.mentions == ["+0987654321"]


def test_parse_message_malformed_json(message_parser: MessageParser) -> None:
    """Test that malformed JSON returns None."""
    raw_message_str = '{"envelope":'
    message = message_parser.parse(raw_message_str)
    assert message is None


@pytest.mark.parametrize(
    "raw_message",
    [
        {},  # Empty JSON object
        {"foo": "bar"},  # Missing 'envelope'
        {"envelope": {}},  # Envelope with no data
        {"envelope": {"unsupportedMessage": {}}},  # Unsupported message type
    ],
)
def test_parse_message_edge_cases(
    message_parser: MessageParser, raw_message: dict
) -> None:
    """Test various edge cases that should result in None."""
    raw_message_str = json.dumps(raw_message)
    message = message_parser.parse(raw_message_str)
    assert message is None


def test_parse_message_with_no_message_body(message_parser: MessageParser) -> None:
    """Test that a dataMessage with no actual message content is handled."""
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": TIMESTAMP,
            "dataMessage": {
                "timestamp": TIMESTAMP,
                "message": None,  # Explicitly None
            },
        }
    }
    raw_message_str = json.dumps(raw_message)
    message = message_parser.parse(raw_message_str)
    assert message is not None
    assert message.message is None
