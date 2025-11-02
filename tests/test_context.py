from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient
from signal_client.context import Context
from signal_client.domain.message import Message, MessageType


@pytest.mark.asyncio
async def test_context_send(bot: SignalClient):
    """Test that context.send calls the API service correctly."""
    # Arrange
    message = Message(
        message="test",
        source="user1",
        timestamp=1,
        type=MessageType.DATA_MESSAGE,
    )
    context = Context(
        message,
        bot.container.api_service(),
        bot.container.config.phone_number(),
    )

    # Act
    await context.send("hello")

    # Assert
    send_mock = cast("AsyncMock", bot.container.api_service().messages.send)
    (request,) = send_mock.call_args.args
    assert request["message"] == "hello"
    assert request["recipients"] == ["user1"]


@pytest.mark.asyncio
async def test_context_reply(bot: SignalClient):
    """Test that context.reply calls the API service correctly."""
    # Arrange
    message = Message(
        message="test",
        source="user1",
        timestamp=1,
        type=MessageType.DATA_MESSAGE,
    )
    context = Context(
        message,
        bot.container.api_service(),
        bot.container.config.phone_number(),
    )

    # Act
    await context.reply("hello")

    # Assert
    send_mock = cast("AsyncMock", bot.container.api_service().messages.send)
    (request,) = send_mock.call_args.args
    assert request["message"] == "hello"
    assert request["recipients"] == ["user1"]
    assert request["quote_author"] == "user1"
    assert request["quote_message"] == "test"
    assert request["quote_timestamp"] == 1
