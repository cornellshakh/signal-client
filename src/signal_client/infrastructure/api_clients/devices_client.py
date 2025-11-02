from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class DevicesClient(BaseClient):
    async def get_devices(self, phone_number: str) -> list[dict[str, Any]]:
        """List linked devices."""
        response = await self._make_request("GET", f"/v1/devices/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def add_device(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Links another device to this device."""
        response = await self._make_request(
            "POST", f"/v1/devices/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_qrcodelink(self) -> dict[str, Any]:
        """Link device and generate QR code."""
        response = await self._make_request("GET", "/v1/qrcodelink")
        return cast("dict[str, Any]", response)

    async def register(self, phone_number: str) -> dict[str, Any]:
        """Register a phone number."""
        response = await self._make_request("POST", f"/v1/register/{phone_number}")
        return cast("dict[str, Any]", response)

    async def verify(self, phone_number: str, token: str) -> dict[str, Any]:
        """Verify a registered phone number."""
        response = await self._make_request(
            "POST", f"/v1/register/{phone_number}/verify/{token}"
        )
        return cast("dict[str, Any]", response)

    async def unregister(self, phone_number: str) -> dict[str, Any]:
        """Unregister a phone number."""
        response = await self._make_request("POST", f"/v1/unregister/{phone_number}")
        return cast("dict[str, Any]", response)
