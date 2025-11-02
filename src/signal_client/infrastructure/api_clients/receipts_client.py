from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ReceiptsClient(BaseClient):
    async def send_receipt(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a receipt."""
        response = await self._make_request(
            "POST", f"/v1/receipts/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
