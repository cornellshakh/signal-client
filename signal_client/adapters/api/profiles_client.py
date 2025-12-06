"""Profiles API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ProfilesClient(BaseClient):
    """Client for interacting with the Signal Profiles API.

    Provides methods for managing user profiles, primarily focused on updates.
    """

    async def get_profile(self, phone_number: str) -> dict[str, Any]:
        """Retrieve a user profile.

        Note: The Signal REST API currently does not support direct retrieval
        of profiles. This method is included for completeness but will raise
        a NotImplementedError. Profile updates should be pushed using `update_profile`.

        Args:
            phone_number: The phone number of the account.

        Raises:
            NotImplementedError: Raised because profile retrieval is not
                supported by the API.

        """
        msg = (
            "Retrieving profiles via REST is not supported. "
            "Use update_profile to push profile changes instead."
        )
        raise NotImplementedError(msg)

    async def update_profile(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a user's profile.

        Args:
            phone_number: Phone number of the account whose profile is being
                updated.
            data: A dictionary containing the profile data to update.

        Returns:
            A dictionary confirming the profile update.

        """
        response = await self._make_request(
            "PUT", f"/v1/profiles/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_profile_avatar(self, phone_number: str) -> bytes:
        """Retrieve a user's profile avatar.

        Note: The Signal REST API currently does not support direct retrieval
        of profile avatars. This method is included for completeness but will raise
        a NotImplementedError. Avatar updates should be pushed as a base64 payload
        within `update_profile`.

        Args:
            phone_number: The phone number of the account.

        Raises:
            NotImplementedError: Raised because profile avatar retrieval is not
                supported by the API.

        """
        msg = (
            "Retrieving profile avatars via REST is not supported. "
            "Use update_profile with a base64 avatar payload instead."
        )
        raise NotImplementedError(msg)
