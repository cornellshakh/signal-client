from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class SearchClient(BaseClient):
    async def search_registered_numbers(
        self, phone_number: str, numbers: list[str]
    ) -> list[dict[str, Any]]:
        """Check if numbers are registered."""
        response = await self._make_request(
            "GET", f"/v1/search/{phone_number}", params={"numbers": numbers}
        )
        return cast("list[dict[str, Any]]", response)
