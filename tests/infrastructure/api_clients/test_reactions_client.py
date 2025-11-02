from __future__ import annotations

from typing import Any

import pytest

from signal_client.infrastructure.api_clients.reactions_client import ReactionsClient


@pytest.mark.asyncio
async def test_send_reaction(
    reactions_client: ReactionsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    reaction_data = {
        "recipient": "+0987654321",
        "action": "react",
        "emoji": "👍",
    }
    aresponses.add(
        "localhost:8080",
        f"/v1/reactions/{phone_number}",
        "POST",
        aresponses.Response(status=201),
    )
    await reactions_client.send_reaction(phone_number, reaction_data)


@pytest.mark.asyncio
async def test_remove_reaction(
    reactions_client: ReactionsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    reaction_data = {
        "recipient": "+0987654321",
        "action": "react",
        "emoji": "👍",
    }
    aresponses.add(
        "localhost:8080",
        f"/v1/reactions/{phone_number}",
        "DELETE",
        aresponses.Response(status=204),
    )
    await reactions_client.remove_reaction(phone_number, reaction_data)
