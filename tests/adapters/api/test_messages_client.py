"""Tests for the MessagesClient."""

from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.adapters.api.messages_client import MessagesClient
from signal_client.adapters.api.schemas.requests import SendMessageRequest


@pytest.mark.asyncio
async def test_send(
    messages_client: MessagesClient, aresponses: ResponsesMockServer
) -> None:
    """Test sending a message."""
    request = SendMessageRequest(
        number="+1234567890",
        recipients=["+0987654321"],
        message="Hello",
    )
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", "/v2/send"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=201)),
    )
    await messages_client.send(request.model_dump())
