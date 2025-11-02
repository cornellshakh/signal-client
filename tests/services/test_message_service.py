from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from signal_client.domain.message import Message, MessageType
from signal_client.services.message_service import MessageService


@pytest.fixture
def message_service():
    mock_websocket_client = MagicMock()
    mock_queue = AsyncMock()
    return MessageService(mock_websocket_client, mock_queue)


def test_parse_message_simple_text(message_service: MessageService):
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "sourceNumber": "+1234567890",
            "sourceUuid": "some-uuid",
            "sourceName": "Test User",
            "sourceDevice": 1,
            "timestamp": 1672531200000,
            "dataMessage": {
                "timestamp": 1672531200000,
                "message": "Hello, world!",
                "expiresInSeconds": 0,
                "viewOnce": False,
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_service._parse_message(raw_message_str)

    assert isinstance(message, Message)
    assert message.message == "Hello, world!"
    assert message.source == "+1234567890"
    assert message.timestamp == 1672531200000

def test_parse_message_sync_message(message_service: MessageService):
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "sourceNumber": "+1234567890",
            "sourceUuid": "some-uuid",
            "sourceName": "Test User",
            "sourceDevice": 1,
            "timestamp": 1672531200000,
            "syncMessage": {
                "sentMessage": {
                    "timestamp": 1672531200000,
                    "message": "Hello from another device",
                    "expiresInSeconds": 0,
                    "viewOnce": False,
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.message == "Hello from another device"
    assert message.type == MessageType.SYNC_MESSAGE


def test_parse_message_edit_message(message_service: MessageService):
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531201000,
            "dataMessage": {
                "editMessage": {
                    "targetSentTimestamp": 1672531200000,
                    "dataMessage": {"message": "Hello, edited world!"},
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.message == "Hello, edited world!"
    assert message.type == MessageType.EDIT_MESSAGE
    assert message.target_sent_timestamp == 1672531200000


def test_parse_message_remote_delete(message_service: MessageService):
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531202000,
            "dataMessage": {"remoteDelete": {"timestamp": 1672531200000}},
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.type == MessageType.DELETE_MESSAGE
    assert message.remote_delete_timestamp == 1672531200000


def test_parse_message_reaction(message_service: MessageService):
    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1672531203000,
            "dataMessage": {
                "reaction": {
                    "emoji": "👍",
                    "targetAuthor": "+0987654321",
                    "targetSentTimestamp": 1672531200000,
                }
            },
        }
    }
    raw_message_str = json.dumps(raw_message)

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.reaction_emoji == "👍"
    assert message.reaction_target_author == "+0987654321"
    assert message.reaction_target_timestamp == 1672531200000


def test_parse_message_group_message(message_service: MessageService):
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

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.message == "Hello, group!"
    assert message.group == "some-group-id"
    assert message.is_group() is True
    assert message.is_private() is False

def test_parse_message_attachment(message_service: MessageService):
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

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.attachments_local_filenames == ["test.txt"]


def test_parse_message_mention(message_service: MessageService):
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

    message = message_service._parse_message(raw_message_str)

    assert message is not None
    assert message.mentions == ["+0987654321"]