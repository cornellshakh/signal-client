from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient


@pytest.fixture
def mock_env_vars() -> Iterator[None]:
    """Mock environment variables for testing."""
    with mock.patch.dict(
        "os.environ",
        {
            "SIGNAL_PHONE_NUMBER": "+1234567890",
            "SIGNAL_SERVICE_URL": "http://localhost:8080",
            "SIGNAL_API_URL": "http://localhost:8080/v1",
        },
        clear=True,
    ):
        yield


@pytest.fixture
async def bot(mock_env_vars: None) -> AsyncGenerator[SignalClient, None]:
    """Provide a bot instance with a mocked api_service."""
    _ = mock_env_vars
    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
        "worker_pool_size": 1,
    }
    bot = SignalClient(config)
    bot.container.api_client_container.accounts_client.override(AsyncMock())
    bot.container.api_client_container.attachments_client.override(AsyncMock())
    bot.container.api_client_container.contacts_client.override(AsyncMock())
    bot.container.api_client_container.devices_client.override(AsyncMock())
    bot.container.api_client_container.general_client.override(AsyncMock())
    bot.container.api_client_container.groups_client.override(AsyncMock())
    bot.container.api_client_container.identities_client.override(AsyncMock())
    bot.container.api_client_container.messages_client.override(AsyncMock())
    bot.container.api_client_container.profiles_client.override(AsyncMock())
    bot.container.api_client_container.reactions_client.override(AsyncMock())
    bot.container.api_client_container.receipts_client.override(AsyncMock())
    bot.container.api_client_container.search_client.override(AsyncMock())
    bot.container.api_client_container.sticker_packs_client.override(AsyncMock())
    yield bot
    await bot.shutdown()
