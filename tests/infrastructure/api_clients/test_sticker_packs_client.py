from __future__ import annotations

from typing import Any

import pytest

from signal_client.infrastructure.api_clients.sticker_packs_client import (
    StickerPacksClient,
)


@pytest.mark.asyncio
async def test_get_sticker_packs(
    sticker_packs_client: StickerPacksClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    aresponses.add(
        "localhost:8080",
        f"/v1/sticker-packs/{phone_number}",
        "GET",
        aresponses.Response(status=200),
    )
    await sticker_packs_client.get_sticker_packs(phone_number)


@pytest.mark.asyncio
async def test_add_sticker_pack(
    sticker_packs_client: StickerPacksClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    pack_data = {"pack_id": "test_pack"}
    aresponses.add(
        "localhost:8080",
        f"/v1/sticker-packs/{phone_number}",
        "POST",
        aresponses.Response(status=201),
    )
    await sticker_packs_client.add_sticker_pack(phone_number, pack_data)
