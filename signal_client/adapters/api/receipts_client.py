"""Receipts API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ReceiptsClient(BaseClient):
    """Client for interacting with the Signal Receipts API.

    Provides methods for sending receipts to messages.
    """

    async def send_receipt(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a receipt for a message.

        Args:
            phone_number: The phone number of the account sending the receipt.
            data: A dictionary containing the receipt details.

        Returns:
            A dictionary confirming the receipt was sent.

        """
        response = await self._make_request(
            "POST", f"/v1/receipts/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
