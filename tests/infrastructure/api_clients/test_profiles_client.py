from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.infrastructure.api_clients.profiles_client import ProfilesClient


@pytest.mark.asyncio
async def test_update_profile(
    profiles_client: ProfilesClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    profile_data = {"name": "test"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/profiles/{phone_number}"),
        cast("Pattern[str]", "PUT"),
        cast("Any", aresponses.Response(status=204)),
    )
    await profiles_client.update_profile(phone_number, profile_data)
