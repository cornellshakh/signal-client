"""Tests for the bot module."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
import structlog

from signal_client import SignalClient
from signal_client.adapters.api.schemas.requests import SendMessageRequest
from signal_client.app import bot as bot_module
from signal_client.core.command import command
from signal_client.core.context import Context
from signal_client.runtime.models import QueuedMessage

# Define a type alias for a structlog processor
Processor = Callable[[Any, str, MutableMapping[str, Any]], Any]


async def send_message(bot: SignalClient, text: str) -> None:
    """Simulate sending a message to the bot."""
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
    await bot.queue.put(
        QueuedMessage(
            raw=json.dumps(message),
            enqueued_at=time.perf_counter(),
        )
    )


def assert_sent(bot: SignalClient, text: str) -> None:
    """Assert that a message was sent by the bot."""
    send_mock = cast("MagicMock", bot.api_clients.messages.send)
    (request,) = send_mock.call_args.args
    assert request["message"] == text


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
async def test_bot_registers_and_handles_command(bot: SignalClient) -> None:
    """Test that the bot registers a command and handles it correctly."""
    # Arrange
    command_handled = asyncio.Event()

    @command("!ping")
    async def ping_command(context: Context) -> None:
        request = SendMessageRequest(message="pong", recipients=[])
        await context.send(request)
        command_handled.set()

    bot.register(ping_command)

    # Act
    worker_pool_manager = bot.worker_pool
    worker_pool_manager.start()
    await send_message(bot, "!ping")
    await asyncio.wait_for(command_handled.wait(), timeout=1)

    # Assert
    assert_sent(bot, "pong")

    # Clean up
    worker_pool_manager.stop()
    await worker_pool_manager.join()


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
async def test_signal_client_async_context_manager() -> None:
    """Test the SignalClient as an asynchronous context manager."""
    async with SignalClient() as client:
        session = client.app.session
        assert session is not None
        session = cast("aiohttp.ClientSession", session)
        assert not session.closed

    assert session.closed


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
async def test_signal_client_use_registers_middleware() -> None:
    """Test that SignalClient.use registers middleware correctly."""
    events = []

    async def middleware(
        context: Context, nxt: Callable[[Context], Awaitable[None]]
    ) -> None:
        events.append("middleware")
        await nxt(context)

    bot = SignalClient()
    await bot.app.initialize()

    @command("!ping")
    async def ping_command(_context: Context) -> None:
        events.append("handler")

    bot.register(ping_command)
    bot.use(middleware)

    worker_pool_manager = bot.worker_pool
    worker_pool_manager.start()
    await send_message(bot, "!ping")
    await asyncio.sleep(0)
    await bot.queue.join()
    worker_pool_manager.stop()
    await worker_pool_manager.join()

    assert events == ["middleware", "handler"]
    await bot.shutdown()


@pytest.mark.usefixtures("mock_env_vars")
def test_signal_client_respects_existing_structlog_configuration() -> None:
    """Test that SignalClient respects existing structlog configurations."""
    structlog.reset_defaults()
    bot_module.reset_structlog_configuration_for_tests()

    original_processors: list[Processor] = [
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.render_to_log_kwargs,
    ]
    structlog.configure(processors=original_processors)

    client = SignalClient()
    assert client.settings.phone_number == "+1234567890"
    asyncio.run(client.shutdown())

    configured_processors = structlog.get_config().get("processors")
    assert configured_processors == original_processors

    structlog.reset_defaults()
    bot_module.reset_structlog_configuration_for_tests()


@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_env_vars")
async def test_signal_client_start_propagates_exceptions() -> None:
    """Test that SignalClient.start propagates exceptions."""
    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "worker_pool_size": 0,
    }

    client = SignalClient(config)
    await client.app.initialize()

    assert client.app.message_service is not None
    client.app.message_service.listen = AsyncMock(  # type: ignore[assignment]
        side_effect=RuntimeError("listen failed")
    )

    mock_websocket_client = AsyncMock()
    mock_websocket_client.close = AsyncMock()
    await client.set_websocket_client(mock_websocket_client)

    with pytest.raises(RuntimeError, match="listen failed"):
        await client.start()

    await client.shutdown()
