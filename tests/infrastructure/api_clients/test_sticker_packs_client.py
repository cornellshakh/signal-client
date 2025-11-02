from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.infrastructure.api_clients.sticker_packs_client import (
    StickerPacksClient,
)


@pytest.mark.asyncio
async def test_get_sticker_packs(
    sticker_packs_client: StickerPacksClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/sticker-packs/{phone_number}"),
        cast("Pattern[str]", "GET"),
        cast("Any", aresponses.Response(status=200)),
    )
    await sticker_packs_client.get_sticker_packs(phone_number)


@pytest.mark.asyncio
async def test_add_sticker_pack(
    sticker_packs_client: StickerPacksClient, aresponses: ResponsesMockServer
) -> None:
    phone_number = "+1234567890"
    pack_data = {"pack_id": "test_pack"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/sticker-packs/{phone_number}"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=201)),
    )
    await sticker_packs_client.add_sticker_pack(phone_number, pack_data)
