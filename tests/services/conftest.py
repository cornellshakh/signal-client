from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from signal_client import SignalClient
from signal_client.infrastructure.schemas.message import Message


@pytest_asyncio.fixture
async def bot(mock_env_vars: None) -> AsyncGenerator[SignalClient, None]:
    """Return a SignalClient instance."""
    _ = mock_env_vars
    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "storage_type": "sqlite",
        "sqlite_database": ":memory:",
    }
    bot = SignalClient(config=config)
    yield bot
    await bot.shutdown()


@pytest.fixture
def message_queue() -> asyncio.Queue[Message]:
    """Return a message queue."""
    return asyncio.Queue()
