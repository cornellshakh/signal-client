"""Device API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class DevicesClient(BaseClient):
    """Client for interacting with the Signal Devices API.

    Provides methods for managing linked devices, registering/unregistering
    phone numbers, and verifying registrations.
    """

    async def get_devices(self, phone_number: str) -> list[dict[str, Any]]:
        """Retrieve a list of linked devices for a given phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A list of dictionaries, each representing a linked device.

        """
        response = await self._make_request("GET", f"/v1/devices/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def add_device(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Link another device to this device.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the device linking details.

        Returns:
            A dictionary confirming the device has been linked.

        """
        response = await self._make_request(
            "POST", f"/v1/devices/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_device(self, phone_number: str, device_id: str) -> dict[str, Any]:
        """Remove a linked device from the account.

        Args:
            phone_number: The phone number of the account.
            device_id: The ID of the device to remove.

        Returns:
            A dictionary confirming the device has been removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/devices/{phone_number}/{device_id}"
        )
        return cast("dict[str, Any]", response)

    async def get_qrcodelink(self) -> dict[str, Any]:
        """Generate a QR code link for device linking.

        Returns:
            A dictionary containing the QR code linking information.

        """
        response = await self._make_request("GET", "/v1/qrcodelink")
        return cast("dict[str, Any]", response)

    async def register(self, phone_number: str) -> dict[str, Any]:
        """Register a phone number with the Signal service.

        Args:
            phone_number: The phone number to register.

        Returns:
            A dictionary confirming the registration request.

        """
        response = await self._make_request("POST", f"/v1/register/{phone_number}")
        return cast("dict[str, Any]", response)

    async def verify(self, phone_number: str, token: str) -> dict[str, Any]:
        """Verify a registered phone number using a verification token.

        Args:
            phone_number: The phone number to verify.
            token: The verification token received.

        Returns:
            A dictionary confirming the verification.

        """
        response = await self._make_request(
            "POST", f"/v1/register/{phone_number}/verify/{token}"
        )
        return cast("dict[str, Any]", response)

    async def unregister(self, phone_number: str) -> dict[str, Any]:
        """Unregister a phone number from the Signal service.

        Args:
            phone_number: The phone number to unregister.

        Returns:
            A dictionary confirming the unregistration.

        """
        response = await self._make_request("POST", f"/v1/unregister/{phone_number}")
        return cast("dict[str, Any]", response)
