"""Account management client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class AccountsClient(BaseClient):
    """Client for interacting with the Signal Account API.

    Provides methods for managing account settings, PINs, usernames,
    and other account-related operations.
    """

    async def get_accounts(self) -> list[dict[str, Any]]:
        """Retrieve a list of all configured accounts.

        Returns:
            A list of dictionaries, each representing an account.

        """
        response = await self._make_request("GET", "/v1/accounts")
        return cast("list[dict[str, Any]]", response)

    async def get_account(self, phone_number: str) -> dict[str, Any]:
        """Retrieve information about a specific account.

        Args:
            phone_number: The phone number of the account to retrieve.

        Returns:
            A dictionary containing information about the account.

        """
        response = await self._make_request("GET", f"/v1/accounts/{phone_number}")
        return cast("dict[str, Any]", response)

    async def set_device_name(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the device name for a given account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the new device name.

        Returns:
            A dictionary confirming the device name update.

        """
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/device-name", json=data
        )
        return cast("dict[str, Any]", response)

    async def set_pin(self, phone_number: str, data: dict[str, Any]) -> dict[str, Any]:
        """Set a PIN for the account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the PIN details.

        Returns:
            A dictionary confirming the PIN has been set.

        """
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/pin", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_pin(self, phone_number: str) -> dict[str, Any]:
        """Remove the PIN from the account.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary confirming the PIN has been removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/pin"
        )
        return cast("dict[str, Any]", response)

    async def set_registration_lock_pin(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set a registration lock PIN for the account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the registration lock PIN.

        Returns:
            A dictionary confirming the registration lock PIN has been set.

        """
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/registration-lock", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_registration_lock_pin(self, phone_number: str) -> dict[str, Any]:
        """Remove the registration lock PIN from the account.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary confirming the registration lock PIN has been removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/registration-lock"
        )
        return cast("dict[str, Any]", response)

    async def lift_rate_limit(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Lift rate limit restrictions for the account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing rate limit challenge details.

        Returns:
            A dictionary confirming the rate limit has been lifted.

        """
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/rate-limit-challenge", json=data
        )
        return cast("dict[str, Any]", response)

    async def update_settings(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update the account settings.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the settings to update.

        Returns:
            A dictionary confirming the settings update.

        """
        response = await self._make_request(
            "PUT", f"/v1/accounts/{phone_number}/settings", json=data
        )
        return cast("dict[str, Any]", response)

    async def set_username(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set a username for the account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the new username.

        Returns:
            A dictionary confirming the username update.

        """
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/username", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_username(self, phone_number: str) -> dict[str, Any]:
        """Remove the username from the account.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary confirming the username has been removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/username"
        )
        return cast("dict[str, Any]", response)
