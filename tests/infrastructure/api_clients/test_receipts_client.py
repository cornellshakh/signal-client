from __future__ import annotations

from typing import Any

import pytest

from signal_client.infrastructure.api_clients.receipts_client import ReceiptsClient


@pytest.mark.asyncio
async def test_send_receipt(
    receipts_client: ReceiptsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    receipt_data = {"recipient": "+0987654321"}
    aresponses.add(
        "localhost:8080",
        f"/v1/receipts/{phone_number}",
        "POST",
        aresponses.Response(status=201),
    )
    await receipts_client.send_receipt(phone_number, receipt_data)
