from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ReactionsClient(BaseClient):
    async def send_reaction(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a reaction."""
        response = await self._make_request(
            "POST", f"/v1/reactions/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_reaction(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Remove a reaction."""
        response = await self._make_request(
            "DELETE", f"/v1/reactions/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
