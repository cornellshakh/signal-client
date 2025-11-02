from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.domain.messages import SendMessageRequest
from signal_client.infrastructure.api_clients.messages_client import MessagesClient


@pytest.mark.asyncio
async def test_send(
    messages_client: MessagesClient, aresponses: ResponsesMockServer
) -> None:
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
