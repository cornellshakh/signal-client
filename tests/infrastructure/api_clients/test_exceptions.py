from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from yarl import URL

from signal_client.exceptions import (
    AuthenticationError,
    GroupNotFoundError,
    InvalidRecipientError,
    RateLimitError,
    ServerError,
    SignalAPIError,
)
from signal_client.infrastructure.api_clients.base_client import (
    BaseClient,
    ClientConfig,
)


def _make_base_client() -> BaseClient:
    session = AsyncMock(spec=aiohttp.ClientSession)
    config = ClientConfig(session=session, base_url="http://localhost")
    return BaseClient(config)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, expected_exception",
    [
        (401, AuthenticationError),
        (413, RateLimitError),
        (429, RateLimitError),
        (500, ServerError),
    ],
)
async def test_raise_for_status_maps_status_codes(
    status: int, expected_exception: type[Exception]
):
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = status
    response.reason = "Test reason"
    response.url = URL("http://localhost/messages")
    response.text = AsyncMock(return_value="{}")

    with pytest.raises(expected_exception):
        await client._raise_for_status(response)


@pytest.mark.asyncio
async def test_raise_for_status_handles_invalid_recipient():
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 404
    response.reason = "Not Found"
    response.url = URL("http://localhost/messages")
    response.text = AsyncMock(return_value="{}")

    with pytest.raises(InvalidRecipientError):
        await client._raise_for_status(response)


@pytest.mark.asyncio
async def test_raise_for_status_handles_group_not_found():
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 404
    response.reason = "Not Found"
    response.url = URL("http://localhost/groups/1234")
    response.text = AsyncMock(return_value="{}")

    with pytest.raises(GroupNotFoundError):
        await client._raise_for_status(response)


@pytest.mark.asyncio
async def test_raise_for_status_falls_back_to_signal_api_error():
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 418
    response.reason = "I'm a teapot"
    response.url = URL("http://localhost/teapot")
    response.text = AsyncMock(return_value="{}")

    with pytest.raises(SignalAPIError) as exc_info:
        await client._raise_for_status(response)

    assert "I'm a teapot" in str(exc_info.value)
