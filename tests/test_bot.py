import asyncio
from typing import ClassVar, cast
from unittest.mock import MagicMock

import pytest

from signal_client import SignalClient
from signal_client.command import Command
from signal_client.context import Context
from signal_client.domain.message import Message, MessageType


async def send_message(bot: SignalClient, text: str):
    """Helper to simulate sending a message to the bot."""
    message = Message(
        message=text,
        source="user1",
        group="group1",
        timestamp=1672531200000,
        type=MessageType.DATA_MESSAGE,
    )
    await bot.container.message_queue().put(message)


def assert_sent(bot: SignalClient, text: str):
    """Helper to assert that a message was sent by the bot."""
    send_mock = cast("MagicMock", bot.container.api_service().messages.send)
    (request,) = send_mock.call_args.args
    assert request["message"] == text
    assert request["number"] == bot.container.config.phone_number()


@pytest.mark.asyncio
async def test_bot_registers_and_handles_command(bot: SignalClient):
    """Test that the bot registers a command and handles it correctly."""
    # Arrange
    command_handled = asyncio.Event()

    class PingCommand(Command):
        triggers: ClassVar[list[str]] = ["!ping"]
        whitelisted: ClassVar[list[str]] = []
        case_sensitive = False

        async def handle(self, context: Context) -> None:
            await context.send("pong")
            command_handled.set()

    bot.register(PingCommand())

    # Act
    task = asyncio.create_task(bot.container.command_service().process_messages())
    await send_message(bot, "!ping")
    await asyncio.wait_for(command_handled.wait(), timeout=1)

    # Assert
    assert_sent(bot, "pong")

    # Clean up
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
