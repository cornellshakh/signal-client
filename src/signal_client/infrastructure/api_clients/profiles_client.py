from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ProfilesClient(BaseClient):
    async def get_profile(self, phone_number: str) -> dict[str, Any]:
        """Get a profile."""
        response = await self._make_request("GET", f"/v1/profiles/{phone_number}")
        return cast("dict[str, Any]", response)

    async def update_profile(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update Profile."""
        response = await self._make_request(
            "PUT", f"/v1/profiles/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_profile_avatar(self, phone_number: str) -> bytes:
        """Get a profile avatar."""
        response = await self._make_request(
            "GET",
            f"/v1/profiles/{phone_number}/avatar",
        )
        return cast("bytes", response)
