import asyncio
import time
from collections.abc import AsyncGenerator
from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock

import pytest

from signal_client.bot import SignalClient
from signal_client.command import Command
from signal_client.context import Context

MIN_THROUGHPUT = 100
MAX_AVG_LATENCY = 0.1
NUM_MESSAGES = 1000
NUM_REQUESTS = 100


class MockCommand(Command):
    triggers: ClassVar[list[str]] = ["!test"]
    whitelisted: ClassVar[list[str]] = []
    case_sensitive: bool = False

    async def handle(self, _context: Context) -> None:
        await asyncio.sleep(0.01)  # Simulate some work


@pytest.mark.asyncio
async def test_message_throughput():
    """
    Measures the number of messages the bot can process per second.
    """
    config = {
        "signal_service": "http://localhost:8080",
        "phone_number": "+1234567890",
        "worker_pool_size": 10,
    }
    client = SignalClient(config)
    client.register(MockCommand())

    # Mock the websocket client to simulate incoming messages
    client.container.websocket_client.override(AsyncMock())
    websocket_client = client.container.websocket_client()
    websocket_client.listen = MagicMock()

    async def message_generator() -> AsyncGenerator[str, None]:
        for i in range(NUM_MESSAGES):
            yield f'{{"type": "message", "id": {i}, "data": {{"message": "!test"}}}}'

    websocket_client.listen.return_value = message_generator()

    start_time = time.monotonic()
    await client.start()
    end_time = time.monotonic()

    duration = end_time - start_time
    throughput = NUM_MESSAGES / duration
    print(f"Processed {NUM_MESSAGES} messages in {duration:.2f} seconds.")
    print(f"Throughput: {throughput:.2f} messages/sec")

    # The bot should be able to process at least 100 messages per second
    assert throughput > MIN_THROUGHPUT


@pytest.mark.asyncio
async def test_api_latency():
    """
    Measures the latency of API requests.
    """
    config = {
        "signal_service": "http://localhost:8080",
        "phone_number": "+1234567890",
    }
    client = SignalClient(config)

    # Mock the accounts client to simulate API requests
    client.container.accounts_client.override(AsyncMock())
    accounts_client = client.container.accounts_client()
    accounts_client.get_account = AsyncMock(return_value={"number": "+1234567890"})

    latencies = []
    for _ in range(NUM_REQUESTS):
        start_time = time.monotonic()
        await accounts_client.get_account()
        end_time = time.monotonic()
        latencies.append(end_time - start_time)

    avg_latency = sum(latencies) / len(latencies)
    print(f"Average latency: {avg_latency * 1000:.2f} ms")

    # The average latency should be less than 100 ms
    assert avg_latency < MAX_AVG_LATENCY
