import asyncio
import json
from typing import ClassVar, cast
from unittest.mock import MagicMock

import pytest

from signal_client import SignalClient
from signal_client.command import Command
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest


async def send_message(bot: SignalClient, text: str):
    """Helper to simulate sending a message to the bot."""
    message = {
        "envelope": {
            "source": "user1",
            "timestamp": 1672531200000,
            "dataMessage": {
                "message": text,
                "groupInfo": {"groupId": "group1"},
            },
        }
    }
    await bot.container.message_queue().put(json.dumps(message))


def assert_sent(bot: SignalClient, text: str):
    """Helper to assert that a message was sent by the bot."""
    send_mock = cast("MagicMock", bot.container.messages_client().send)
    (request,) = send_mock.call_args.args
    assert request["message"] == text


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
            request = SendMessageRequest(message="pong", recipients=[])
            await context.send(request)
            command_handled.set()

    bot.register(PingCommand())

    # Act
    worker_pool_manager = bot.container.worker_pool_manager()
    worker_pool_manager.start(bot.container)
    await send_message(bot, "!ping")
    await asyncio.wait_for(command_handled.wait(), timeout=1)

    # Assert
    assert_sent(bot, "pong")

    # Clean up
    worker_pool_manager.stop()
    await worker_pool_manager.join()
