from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio

from signal_client import SignalClient
from signal_client.container import Container
from signal_client.domain.message import Message


@pytest_asyncio.fixture
async def bot() -> AsyncGenerator[SignalClient, None]:
    """Return a SignalClient instance."""
    container = Container()
    container.config.from_dict(
        {
            "signal_service": "localhost:8080",
            "phone_number": "+1234567890",
            "storage": {"type": "in-memory"},
        }
    )
    async with aiohttp.ClientSession() as session:
        container.session.override(session)
        yield SignalClient(container=container)


@pytest.fixture
def message_queue() -> asyncio.Queue[Message]:
    """Return a message queue."""
    return asyncio.Queue()
