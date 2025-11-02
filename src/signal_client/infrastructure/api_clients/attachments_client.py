from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class AttachmentsClient(BaseClient):
    async def get_attachments(self) -> list[dict[str, Any]]:
        """List all attachments."""
        response = await self._make_request("GET", "/v1/attachments")
        return cast("list[dict[str, Any]]", response)

    async def get_attachment(self, attachment_id: str) -> bytes:
        """Serve Attachment."""
        response = await self._make_request("GET", f"/v1/attachments/{attachment_id}")
        return cast("bytes", response)

    async def remove_attachment(self, attachment_id: str) -> dict[str, Any]:
        """Remove attachment."""
        response = await self._make_request(
            "DELETE", f"/v1/attachments/{attachment_id}"
        )
        return cast("dict[str, Any]", response)
