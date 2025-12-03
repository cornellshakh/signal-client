from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient
from signal_client.context import Context
from signal_client.context_deps import ContextDependencies


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
    await bot.app.initialize()
    api_clients = bot.api_clients
    api_clients.accounts = AsyncMock()
    api_clients.attachments = AsyncMock()
    api_clients.contacts = AsyncMock()
    api_clients.devices = AsyncMock()
    api_clients.general = AsyncMock()
    api_clients.groups = AsyncMock()
    api_clients.identities = AsyncMock()
    api_clients.messages = AsyncMock()
    api_clients.messages.send.return_value = {"timestamp": "1"}
    api_clients.messages.remote_delete.return_value = {"timestamp": "2"}
    api_clients.profiles = AsyncMock()
    api_clients.reactions = AsyncMock()
    api_clients.receipts = AsyncMock()
    api_clients.search = AsyncMock()
    api_clients.sticker_packs = AsyncMock()
    bot.app.context_dependencies = ContextDependencies(
        accounts_client=api_clients.accounts,
        attachments_client=api_clients.attachments,
        contacts_client=api_clients.contacts,
        devices_client=api_clients.devices,
        general_client=api_clients.general,
        groups_client=api_clients.groups,
        identities_client=api_clients.identities,
        messages_client=api_clients.messages,
        profiles_client=api_clients.profiles,
        reactions_client=api_clients.reactions,
        receipts_client=api_clients.receipts,
        search_client=api_clients.search,
        sticker_packs_client=api_clients.sticker_packs,
        lock_manager=bot.app.lock_manager,
        phone_number=bot.settings.phone_number,
    )
    bot.app.context_factory = lambda message: Context(
        message=message, dependencies=bot.app.context_dependencies
    )
    if bot.app.worker_pool is not None:
        bot.app.worker_pool._context_factory = bot.app.context_factory
    yield bot
    await bot.shutdown()


@pytest.fixture
def context_dependencies(bot: SignalClient) -> ContextDependencies:
    """Build ContextDependencies once so tests don't need to duplicate wiring."""
    return ContextDependencies(
        accounts_client=bot.api_clients.accounts,
        attachments_client=bot.api_clients.attachments,
        contacts_client=bot.api_clients.contacts,
        devices_client=bot.api_clients.devices,
        general_client=bot.api_clients.general,
        groups_client=bot.api_clients.groups,
        identities_client=bot.api_clients.identities,
        messages_client=bot.api_clients.messages,
        profiles_client=bot.api_clients.profiles,
        reactions_client=bot.api_clients.reactions,
        receipts_client=bot.api_clients.receipts,
        search_client=bot.api_clients.search,
        sticker_packs_client=bot.api_clients.sticker_packs,
        lock_manager=bot.app.lock_manager,
        phone_number=bot.settings.phone_number,
    )
