from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class MessagesClient(BaseClient):
    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """Send a signal message."""
        response = await self._make_request("POST", "/v2/send", json=data)
        return cast("dict[str, Any]", response)

    async def get_messages(
        self, phone_number: str, recipient: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get messages from a recipient."""
        path = f"/v1/messages/{phone_number}/{recipient}"
        if limit:
            path += f"?limit={limit}"
        response = await self._make_request("GET", path)
        return cast("list[dict[str, Any]]", response)

    async def remote_delete(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Delete a signal message."""
        response = await self._make_request(
            "DELETE", f"/v1/remote-delete/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def set_typing_indicator(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Show Typing Indicator."""
        response = await self._make_request(
            "PUT", f"/v1/typing-indicator/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def unset_typing_indicator(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Hide Typing Indicator."""
        response = await self._make_request(
            "DELETE", f"/v1/typing-indicator/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
