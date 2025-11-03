from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class StickerPacksClient(BaseClient):
    async def get_sticker_packs(self, phone_number: str) -> list[dict[str, Any]]:
        """List Installed Sticker Packs."""
        response = await self._make_request("GET", f"/v1/sticker-packs/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def add_sticker_pack(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Add Sticker Pack."""
        response = await self._make_request(
            "POST", f"/v1/sticker-packs/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_sticker_pack(
        self, phone_number: str, pack_id: str, sticker_id: str
    ) -> bytes:
        """Get a sticker from a sticker pack."""
        response = await self._make_request(
            "GET", f"/v1/sticker-packs/{phone_number}/{pack_id}/{sticker_id}"
        )
        return cast("bytes", response)
