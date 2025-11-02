from __future__ import annotations

import pytest
from aresponses import ResponsesMock

from signal_client.infrastructure.api_clients.search_client import SearchClient


@pytest.mark.asyncio
async def test_search_registered_numbers(
    search_client: SearchClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    numbers_to_search = ["+0987654321"]
    aresponses.add(
        "localhost:8080",
        f"/v1/search/{phone_number}",
        "GET",
        aresponses.Response(status=200),
    )
    await search_client.search_registered_numbers(phone_number, numbers_to_search)
