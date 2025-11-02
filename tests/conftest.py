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
    }
    bot = SignalClient(config)
    api_service_mock = AsyncMock()
    api_service_mock.messages = AsyncMock()
    api_service_mock.messages.send = AsyncMock()
    bot.container.api_service.override(api_service_mock)
    yield bot
    await bot.shutdown()
