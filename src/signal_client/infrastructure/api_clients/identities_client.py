from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class IdentitiesClient(BaseClient):
    async def get_identities(self, phone_number: str) -> list[dict[str, Any]]:
        """List Identities."""
        response = await self._make_request("GET", f"/v1/identities/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def trust_identity(
        self, phone_number: str, number_to_trust: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Trust Identity."""
        response = await self._make_request(
            "PUT",
            f"/v1/identities/{phone_number}/trust/{number_to_trust}",
            json=data,
        )
        return cast("dict[str, Any]", response)
