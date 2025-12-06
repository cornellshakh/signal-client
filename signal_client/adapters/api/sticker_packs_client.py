"""Sticker packs API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class StickerPacksClient(BaseClient):
    """Client for interacting with the Signal Sticker Packs API.

    Provides methods for managing sticker packs, including listing installed packs,
    adding new packs, and retrieving individual stickers.
    """

    async def get_sticker_packs(self, phone_number: str) -> list[dict[str, Any]]:
        """Retrieve a list of installed sticker packs for a given phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A list of dictionaries, each representing an installed sticker pack.

        """
        response = await self._make_request("GET", f"/v1/sticker-packs/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def add_sticker_pack(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Add a new sticker pack to the account.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing the sticker pack details to add.

        Returns:
            A dictionary confirming the sticker pack addition.

        """
        response = await self._make_request(
            "POST", f"/v1/sticker-packs/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_sticker_pack(
        self, phone_number: str, pack_id: str, sticker_id: str
    ) -> bytes:
        """Retrieve a specific sticker from a sticker pack.

        Args:
            phone_number: The phone number of the account.
            pack_id: The ID of the sticker pack.
            sticker_id: The ID of the sticker within the pack.

        Returns:
            The sticker image as bytes.

        """
        response = await self._make_request(
            "GET", f"/v1/sticker-packs/{phone_number}/{pack_id}/{sticker_id}"
        )
        return cast("bytes", response)
