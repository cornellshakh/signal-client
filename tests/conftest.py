import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
async def bot():
    """Provide a bot instance with a mocked api_service."""
    config = {
        "signal_service": "localhost:8080",
        "phone_number": "+1234567890",
        "worker_pool_size": 1,
    }
    bot = SignalClient(config)
    bot.container.accounts_client.override(AsyncMock())
    bot.container.attachments_client.override(AsyncMock())
    bot.container.contacts_client.override(AsyncMock())
    bot.container.devices_client.override(AsyncMock())
    bot.container.general_client.override(AsyncMock())
    bot.container.groups_client.override(AsyncMock())
    bot.container.identities_client.override(AsyncMock())
    bot.container.messages_client.override(AsyncMock())
    bot.container.profiles_client.override(AsyncMock())
    bot.container.reactions_client.override(AsyncMock())
    bot.container.receipts_client.override(AsyncMock())
    bot.container.search_client.override(AsyncMock())
    bot.container.sticker_packs_client.override(AsyncMock())
    yield bot
    await bot.shutdown()
