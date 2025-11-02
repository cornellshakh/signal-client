from __future__ import annotations

from typing import Any

import pytest

from signal_client.infrastructure.api_clients.identities_client import IdentitiesClient


@pytest.mark.asyncio
async def test_get_identities(
    identities_client: IdentitiesClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    aresponses.add(
        "localhost:8080",
        f"/v1/identities/{phone_number}",
        "GET",
        aresponses.Response(status=200),
    )
    await identities_client.get_identities(phone_number)


@pytest.mark.asyncio
async def test_trust_identity(
    identities_client: IdentitiesClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    number_to_trust = "+0987654321"
    trust_data = {"verified": True}
    aresponses.add(
        "localhost:8080",
        f"/v1/identities/{phone_number}/trust/{number_to_trust}",
        "PUT",
        aresponses.Response(status=204),
    )
    await identities_client.trust_identity(phone_number, number_to_trust, trust_data)
