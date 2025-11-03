from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ContactsClient(BaseClient):
    async def get_contacts(self, phone_number: str) -> list[dict[str, Any]]:
        """List Contacts."""
        response = await self._make_request("GET", f"/v1/contacts/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def update_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update/add a contact."""
        response = await self._make_request(
            "PUT", f"/v1/contacts/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def sync_contacts(self, phone_number: str) -> dict[str, Any]:
        """Sync contacts to linked devices."""
        response = await self._make_request("POST", f"/v1/contacts/{phone_number}/sync")
        return cast("dict[str, Any]", response)

    async def get_contact(self, phone_number: str, uuid: str) -> dict[str, Any]:
        """List a specific contact."""
        response = await self._make_request(
            "GET", f"/v1/contacts/{phone_number}/{uuid}"
        )
        return cast("dict[str, Any]", response)

    async def get_contact_avatar(self, phone_number: str, uuid: str) -> bytes:
        """Returns the avatar of a contact."""
        response = await self._make_request(
            "GET", f"/v1/contacts/{phone_number}/{uuid}/avatar"
        )
        return cast("bytes", response)

    async def block_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Block a contact."""
        response = await self._make_request(
            "POST", f"/v1/contacts/{phone_number}/block", json=data
        )
        return cast("dict[str, Any]", response)

    async def unblock_contact(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Unblock a contact."""
        response = await self._make_request(
            "POST", f"/v1/contacts/{phone_number}/unblock", json=data
        )
        return cast("dict[str, Any]", response)
