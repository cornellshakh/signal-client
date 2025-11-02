from __future__ import annotations

import pytest
from aresponses import ResponsesMock

from signal_client.infrastructure.api_clients.profiles_client import ProfilesClient


@pytest.mark.asyncio
async def test_update_profile(
    profiles_client: ProfilesClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    profile_data = {"name": "test"}
    aresponses.add(
        "localhost:8080",
        f"/v1/profiles/{phone_number}",
        "PUT",
        aresponses.Response(status=204),
    )
    await profiles_client.update_profile(phone_number, profile_data)
