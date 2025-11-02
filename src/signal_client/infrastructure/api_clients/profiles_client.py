from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ProfilesClient(BaseClient):
    async def update_profile(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update Profile."""
        response = await self._make_request(
            "PUT", f"/v1/profiles/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
