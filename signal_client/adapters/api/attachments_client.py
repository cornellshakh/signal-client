"""Attachment client helpers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class AttachmentsClient(BaseClient):
    """Client for interacting with the Signal Attachments API.

    Provides methods for managing message attachments, including retrieving
    and removing them.
    """

    async def get_attachments(self) -> list[dict[str, Any]]:
        """Retrieve a list of all attachments.

        Returns:
            A list of dictionaries, each representing an attachment.

        """
        response = await self._make_request("GET", "/v1/attachments")
        return cast("list[dict[str, Any]]", response)

    async def get_attachment(self, attachment_id: str) -> bytes:
        """Retrieve a specific attachment by its ID.

        Args:
            attachment_id: The ID of the attachment to retrieve.

        Returns:
            The raw bytes of the attachment file.

        """
        response = await self._make_request("GET", f"/v1/attachments/{attachment_id}")
        return cast("bytes", response)

    async def remove_attachment(self, attachment_id: str) -> dict[str, Any]:
        """Remove a specific attachment by its ID.

        Args:
            attachment_id: The ID of the attachment to remove.

        Returns:
            A dictionary confirming the attachment has been removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/attachments/{attachment_id}"
        )
        return cast("dict[str, Any]", response)
