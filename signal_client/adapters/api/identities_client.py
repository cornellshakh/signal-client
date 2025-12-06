"""Identities API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class IdentitiesClient(BaseClient):
    """Client for interacting with the Signal Identities API.

    Provides methods for managing identities, including listing and trusting identities.
    """

    async def get_identities(self, phone_number: str) -> list[dict[str, Any]]:
        """Retrieve a list of identities associated with a phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A list of dictionaries, each representing an identity.

        """
        response = await self._make_request("GET", f"/v1/identities/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def trust_identity(
        self, phone_number: str, number_to_trust: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Trust an identity associated with a given phone number.

        Args:
            phone_number: Phone number of the account performing the trust
                operation.
            number_to_trust: The phone number of the identity to trust.
            data: A dictionary containing details for the trust operation.

        Returns:
            A dictionary confirming the trust operation.

        """
        response = await self._make_request(
            "PUT",
            f"/v1/identities/{phone_number}/trust/{number_to_trust}",
            json=data,
        )
        return cast("dict[str, Any]", response)
