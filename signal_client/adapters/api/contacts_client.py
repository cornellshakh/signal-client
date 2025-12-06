"""Contact API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ContactsClient(BaseClient):
    """Client for interacting with the Signal Contacts API.

    Provides methods for managing contacts, including retrieving, updating,
    syncing, blocking, and unblocking them.
    """

    async def get_contacts(self, phone_number: str) -> list[dict[str, Any]]:
        """Retrieve a list of all contacts for a given phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A list of dictionaries, each representing a contact.

        """
        response = await self._make_request("GET", f"/v1/contacts/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def update_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update or add a contact for a given phone number.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the contact details to update/add.

        Returns:
            A dictionary confirming the contact update.

        """
        response = await self._make_request(
            "PUT", f"/v1/contacts/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def sync_contacts(self, phone_number: str) -> dict[str, Any]:
        """Sync contacts to linked devices for a given phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A dictionary confirming the contact sync.

        """
        response = await self._make_request("POST", f"/v1/contacts/{phone_number}/sync")
        return cast("dict[str, Any]", response)

    async def get_contact(self, phone_number: str, uuid: str) -> dict[str, Any]:
        """Retrieve a specific contact by UUID for a given phone number.

        Args:
            phone_number: The phone number of the account.
            uuid: The UUID of the contact to retrieve.

        Returns:
            A dictionary containing information about the specific contact.

        """
        response = await self._make_request(
            "GET", f"/v1/contacts/{phone_number}/{uuid}"
        )
        return cast("dict[str, Any]", response)

    async def get_contact_avatar(self, phone_number: str, uuid: str) -> bytes:
        """Retrieve the avatar of a specific contact.

        Args:
            phone_number: The phone number of the account.
            uuid: The UUID of the contact whose avatar to retrieve.

        Returns:
            The raw bytes of the contact's avatar image.

        """
        response = await self._make_request(
            "GET", f"/v1/contacts/{phone_number}/{uuid}/avatar"
        )
        return cast("bytes", response)

    async def block_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Block a contact for a given phone number.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the contact details to block.

        Returns:
            A dictionary confirming the contact has been blocked.

        """
        response = await self._make_request(
            "POST", f"/v1/contacts/{phone_number}/block", json=data
        )
        return cast("dict[str, Any]", response)

    async def unblock_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Unblock a contact for a given phone number.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the contact details to unblock.

        Returns:
            A dictionary confirming the contact has been unblocked.

        """
        response = await self._make_request(
            "POST", f"/v1/contacts/{phone_number}/unblock", json=data
        )
        return cast("dict[str, Any]", response)
