from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.infrastructure.api_clients.reactions_client import ReactionsClient


@pytest.mark.asyncio
async def test_send_reaction(
    reactions_client: ReactionsClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    reaction_data = {
        "recipient": "+0987654321",
        "action": "react",
        "emoji": "👍",
    }
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/reactions/{phone_number}"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=201)),
    )
    await reactions_client.send_reaction(phone_number, reaction_data)


@pytest.mark.asyncio
async def test_remove_reaction(
    reactions_client: ReactionsClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    reaction_data = {
        "recipient": "+0987654321",
        "action": "react",
        "emoji": "👍",
    }
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/reactions/{phone_number}"),
        cast("Pattern[str]", "DELETE"),
        cast("Any", aresponses.Response(status=204)),
    )
    await reactions_client.remove_reaction(phone_number, reaction_data)
