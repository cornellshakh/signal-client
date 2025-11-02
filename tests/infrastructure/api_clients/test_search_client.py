from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.infrastructure.api_clients.search_client import SearchClient


@pytest.mark.asyncio
async def test_search_registered_numbers(
    search_client: SearchClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    numbers_to_search = ["+0987654321"]
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/search/{phone_number}"),
        cast("Pattern[str]", "GET"),
        cast("Any", aresponses.Response(status=200)),
    )
    await search_client.search_registered_numbers(phone_number, numbers_to_search)
