from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient
from signal_client.context import Context
from signal_client.context_deps import ContextDependencies
from signal_client.infrastructure.schemas.message import Message, MessageType
from signal_client.infrastructure.schemas.requests import SendMessageRequest


@pytest.mark.asyncio
async def test_context_send(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    """Test that context.send calls the API service correctly."""
    # Arrange
    message = Message(
        message="test",
        source="user1",
        timestamp=1,
        type=MessageType.DATA_MESSAGE,
    )
    context = Context(
        message=message,
        dependencies=context_dependencies,
    )

    # Act
    request = SendMessageRequest(message="hello", recipients=[])
    await context.send(request)

    # Assert
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    (request_dict,) = send_mock.call_args.args
    assert request_dict["message"] == "hello"
    assert request_dict["recipients"] == ["user1"]


@pytest.mark.asyncio
async def test_context_reply(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    """Test that context.reply calls the API service correctly."""
    # Arrange
    message = Message(
        message="test",
        source="user1",
        timestamp=1,
        type=MessageType.DATA_MESSAGE,
    )
    context = Context(
        message=message,
        dependencies=context_dependencies,
    )

    # Act
    request = SendMessageRequest(message="hello", recipients=[])
    await context.reply(request)

    # Assert
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    (request_dict,) = send_mock.call_args.args
    assert request_dict["message"] == "hello"
    assert request_dict["recipients"] == ["user1"]
    assert request_dict["quote_author"] == "user1"
    assert request_dict["quote_message"] == "test"
    assert request_dict["quote_timestamp"] == 1
