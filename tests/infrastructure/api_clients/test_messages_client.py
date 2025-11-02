from __future__ import annotations

import pytest
from aresponses import ResponsesMock

from signal_client.domain.messages import SendMessageRequest
from signal_client.infrastructure.api_clients.messages_client import MessagesClient


@pytest.mark.asyncio
async def test_send(messages_client: MessagesClient, aresponses: ResponsesMock) -> None:
    request = SendMessageRequest(
        number="+1234567890",
        recipients=["+0987654321"],
        message="Hello",
    )
    aresponses.add(
        "localhost:8080",
        "/v2/send",
        "POST",
        aresponses.Response(status=201),
    )
    await messages_client.send(request.model_dump())
