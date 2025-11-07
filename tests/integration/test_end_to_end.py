from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

import pytest
from dependency_injector import providers

from signal_client.bot import SignalClient
from signal_client.command import command
from signal_client.context import Context


class StubWebSocket:
    def __init__(self, messages: list[str]) -> None:
        self._messages = messages

    async def listen(self) -> AsyncGenerator[str, None]:
        for message in self._messages:
            yield message

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_end_to_end_flow(monkeypatch, mock_env_vars):
    processed: list[str] = []
    handled = asyncio.Event()

    @command("!ping")
    async def echo(context: Context) -> None:
        processed.append(context.message.source)
        handled.set()

    websocket_messages = [
        json.dumps(
            {
                "envelope": {
                    "source": "+15550001",
                    "timestamp": 1,
                    "dataMessage": {"message": "!ping", "timestamp": 1},
                }
            }
        )
    ]

    mock_websocket = StubWebSocket(websocket_messages)
    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "storage_type": "sqlite",
        "sqlite_database": ":memory:",
        "worker_pool_size": 1,
    }

    client = SignalClient(config=config)
    client.register(echo)

    client.container.services_container.websocket_client.override(
        providers.Object(mock_websocket)
    )

    task = asyncio.create_task(client.start())
    await asyncio.wait_for(handled.wait(), timeout=2)
    await asyncio.wait_for(
        client.container.services_container.message_queue().join(), timeout=2
    )
    await client.shutdown()
    await task

    assert processed == ["+15550001"]
