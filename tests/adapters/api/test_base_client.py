"""Tests for the BaseClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from signal_client.adapters.api.base_client import (
    BaseClient,
    ClientConfig,
)
from signal_client.exceptions import InvalidRecipientError, SignalAPIError


def _make_base_client() -> BaseClient:
    """Helper to create a BaseClient instance."""
    session = AsyncMock(spec=aiohttp.ClientSession)
    config = ClientConfig(session=session, base_url="http://localhost")
    return BaseClient(config)


@pytest.mark.asyncio
async def test_handle_response_uses_error_code_mapping() -> None:
    """Test that _handle_response uses error code mapping."""
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

    with pytest.raises(SignalAPIError) as exc_info:
        await client._handle_response(response)

    assert exc_info.value.status_code == 409
    response.json.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_response_falls_back_to_status_code() -> None:
    """Test that _handle_response falls back to status code."""
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 404
    response.content_type = "application/json"
    response.json = AsyncMock(return_value={"code": "UNKNOWN", "error": "Missing"})

    with pytest.raises(InvalidRecipientError) as exc:
        await client._handle_response(response)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_handle_response_raises_signal_api_error_for_unmapped() -> None:
    """Test that _handle_response raises SignalAPIError for unmapped errors."""
    client = _make_base_client()
    response = MagicMock(spec=aiohttp.ClientResponse)
    response.status = 400
    response.content_type = "application/json"
    response.json = AsyncMock(return_value={"error": "Bad request"})

    with pytest.raises(SignalAPIError) as exc:
        await client._handle_response(response)

    assert exc.value.status_code == 400
