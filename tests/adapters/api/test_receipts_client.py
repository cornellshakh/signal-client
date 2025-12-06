"""Tests for the ReceiptsClient."""

from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.adapters.api.receipts_client import ReceiptsClient


@pytest.mark.asyncio
async def test_send_receipt(
    receipts_client: ReceiptsClient, aresponses: ResponsesMockServer
) -> None:
    """Test sending a receipt."""
    phone_number = "+1234567890"
    receipt_data = {"recipient": "+0987654321"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/receipts/{phone_number}"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=201)),
    )
    await receipts_client.send_receipt(phone_number, receipt_data)
