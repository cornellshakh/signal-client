from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class GeneralClient(BaseClient):
    async def get_about(self) -> dict[str, Any]:
        """Lists general information about the API."""
        response = await self._make_request("GET", "/v1/about")
        return cast("dict[str, Any]", response)

    async def get_configuration(self) -> dict[str, Any]:
        """List the REST API configuration."""
        response = await self._make_request("GET", "/v1/configuration")
        return cast("dict[str, Any]", response)

    async def set_configuration(self, data: dict[str, Any]) -> dict[str, Any]:
        """Set the REST API configuration."""
        response = await self._make_request("POST", "/v1/configuration", json=data)
        return cast("dict[str, Any]", response)

    async def get_settings(self, phone_number: str) -> dict[str, Any]:
        """List account specific settings."""
        response = await self._make_request(
            "GET", f"/v1/configuration/{phone_number}/settings"
        )
        return cast("dict[str, Any]", response)

    async def set_settings(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set account specific settings."""
        response = await self._make_request(
            "POST", f"/v1/configuration/{phone_number}/settings", json=data
        )
        return cast("dict[str, Any]", response)

    async def get_health(self) -> dict[str, Any]:
        """API Health Check."""
        response = await self._make_request("GET", "/v1/health")
        return cast("dict[str, Any]", response)
