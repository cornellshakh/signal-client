from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from signal_client.exceptions import APIError, ConflictError, NotFoundError
from signal_client.infrastructure.api_clients.base_client import (
    BaseClient,
    ClientConfig,
)


def _make_base_client() -> BaseClient:
    session = AsyncMock(spec=aiohttp.ClientSession)
    config = ClientConfig(session=session, base_url="http://localhost")
    return BaseClient(config)


@pytest.mark.asyncio
async def test_handle_response_uses_error_code_mapping() -> None:
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 409
    response.content_type = "application/json"
    response.json = AsyncMock(
        return_value={
            "code": "USER_NOT_GROUP_MEMBER",
            "error": "User is not a group member",
        }
    )

    with pytest.raises(ConflictError) as exc_info:
        await client._handle_response(response)

    assert exc_info.value.status_code == 409
    response.json.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_response_falls_back_to_status_code() -> None:
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 404
    response.content_type = "application/json"
    response.json = AsyncMock(return_value={"code": "UNKNOWN", "error": "Missing"})

    with pytest.raises(NotFoundError) as exc:
        await client._handle_response(response)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_handle_response_raises_api_error_for_unmapped() -> None:
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 400
    response.content_type = "application/json"
    response.json = AsyncMock(return_value={"error": "Bad request"})

    with pytest.raises(APIError) as exc:
        await client._handle_response(response)

    assert exc.value.status_code == 400
