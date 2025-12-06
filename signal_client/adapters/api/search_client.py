"""Search API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class SearchClient(BaseClient):
    """Client for interacting with the Signal Search API.

    Provides methods for checking if phone numbers are registered with Signal.
    """

    async def search_registered_numbers(
        self, phone_number: str, numbers: list[str]
    ) -> list[dict[str, Any]]:
        """Check if a list of phone numbers are registered with Signal.

        Args:
            phone_number: The phone number of the account initiating the search.
            numbers: A list of phone numbers to check for registration.

        Returns:
            A list of dictionaries, each indicating the registration status of a number.

        """
        response = await self._make_request(
            "GET", f"/v1/search/{phone_number}", params={"numbers": numbers}
        )
        return cast("list[dict[str, Any]]", response)
