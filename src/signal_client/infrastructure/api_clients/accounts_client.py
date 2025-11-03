from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class AccountsClient(BaseClient):
    async def get_accounts(self) -> list[dict[str, Any]]:
        """List all accounts."""
        response = await self._make_request("GET", "/v1/accounts")
        return cast("list[dict[str, Any]]", response)

    async def get_account(self, phone_number: str) -> dict[str, Any]:
        """Get information about a specific account."""
        response = await self._make_request("GET", f"/v1/accounts/{phone_number}")
        return cast("dict[str, Any]", response)

    async def set_device_name(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the device name."""
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/device-name", json=data
        )
        return cast("dict[str, Any]", response)

    async def set_pin(self, phone_number: str, data: dict[str, Any]) -> dict[str, Any]:
        """Set Pin."""
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/pin", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_pin(self, phone_number: str) -> dict[str, Any]:
        """Remove Pin."""
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/pin"
        )
        return cast("dict[str, Any]", response)

    async def set_registration_lock_pin(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set a registration lock PIN."""
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/registration-lock", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_registration_lock_pin(self, phone_number: str) -> dict[str, Any]:
        """Remove a registration lock PIN."""
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/registration-lock"
        )
        return cast("dict[str, Any]", response)

    async def lift_rate_limit(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Lift rate limit restrictions."""
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/rate-limit-challenge", json=data
        )
        return cast("dict[str, Any]", response)

    async def update_settings(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update the account settings."""
        response = await self._make_request(
            "PUT", f"/v1/accounts/{phone_number}/settings", json=data
        )
        return cast("dict[str, Any]", response)

    async def set_username(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set a username."""
        response = await self._make_request(
            "POST", f"/v1/accounts/{phone_number}/username", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_username(self, phone_number: str) -> dict[str, Any]:
        """Remove a username."""
        response = await self._make_request(
            "DELETE", f"/v1/accounts/{phone_number}/username"
        )
        return cast("dict[str, Any]", response)
