from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ProfilesClient(BaseClient):
    async def get_profile(self, phone_number: str) -> dict[str, Any]:
        """Profiles are update-only in swagger; GET is unsupported."""
        msg = (
            "Retrieving profiles via REST is not supported. "
            "Use update_profile to push profile changes instead."
        )
        raise NotImplementedError(msg)

    async def update_profile(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update Profile."""
        response = await self._make_request(
            "PUT", f"/v1/profiles/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_profile_avatar(self, phone_number: str) -> bytes:
        """Profiles are update-only in swagger; GET is unsupported."""
        msg = (
            "Retrieving profile avatars via REST is not supported. "
            "Use update_profile with a base64 avatar payload instead."
        )
        raise NotImplementedError(msg)
