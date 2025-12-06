"""General API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class GeneralClient(BaseClient):
    """Client for general Signal API interactions.

    Provides methods for retrieving information about the API, managing
    configurations, checking health, and setting account modes/settings.
    """

    async def get_about(self) -> dict[str, Any]:
        """Retrieve general information about the API.

        Returns:
            A dictionary containing general API information.

        """
        response = await self._make_request("GET", "/v1/about")
        return cast("dict[str, Any]", response)

    async def get_configuration(self) -> dict[str, Any]:
        """Retrieve the current REST API configuration.

        Returns:
            A dictionary containing the API configuration.

        """
        response = await self._make_request("GET", "/v1/configuration")
        return cast("dict[str, Any]", response)

    async def set_configuration(self, data: dict[str, Any]) -> dict[str, Any]:
        """Set the REST API configuration.

        Args:
            data: A dictionary containing the configuration settings to apply.

        Returns:
            A dictionary confirming the configuration update.

        """
        response = await self._make_request("POST", "/v1/configuration", json=data)
        return cast("dict[str, Any]", response)

    async def get_mode(self, phone_number: str) -> dict[str, Any]:
        """Retrieve the mode of a specific account.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary indicating the account's mode.

        """
        response = await self._make_request("GET", f"/v1/configuration/{phone_number}")
        return cast("dict[str, Any]", response)

    async def set_mode(self, phone_number: str, data: dict[str, Any]) -> dict[str, Any]:
        """Set the mode of a specific account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the mode to set.

        Returns:
            A dictionary confirming the mode update.

        """
        response = await self._make_request(
            "POST", f"/v1/configuration/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_settings(self, phone_number: str) -> dict[str, Any]:
        """Retrieve account-specific settings.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary containing the account's settings.

        """
        response = await self._make_request(
            "GET", f"/v1/configuration/{phone_number}/settings"
        )
        return cast("dict[str, Any]", response)

    async def set_settings(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set account-specific settings.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the settings to apply.

        Returns:
            A dictionary confirming the settings update.

        """
        response = await self._make_request(
            "POST", f"/v1/configuration/{phone_number}/settings", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_health(self) -> dict[str, Any]:
        """Perform an API health check.

        Returns:
            A dictionary indicating the health status of the API.

        """
        response = await self._make_request("GET", "/v1/health")
        return cast("dict[str, Any]", response)
