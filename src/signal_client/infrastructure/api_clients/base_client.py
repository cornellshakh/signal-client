from __future__ import annotations

from typing import Any

import aiohttp

from signal_client.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    ServerError,
)

HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_SERVER_ERROR = 500


class BaseClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
    ) -> None:
        self._session = session
        self._base_url = base_url

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        if response.status == HTTP_STATUS_UNAUTHORIZED:
            raise AuthenticationError
        if response.status == HTTP_STATUS_NOT_FOUND:
            raise NotFoundError
        if response.status >= HTTP_STATUS_SERVER_ERROR:
            msg = f"Server error: {response.status}"
            raise ServerError(msg)
        if response.status >= HTTP_STATUS_BAD_REQUEST:
            msg = f"API error: {response.status}"
            raise APIError(msg)

        if response.content_type == "application/json":
            return await response.json()
        return await response.read()

    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(method, url, **kwargs) as response:
                return await self._handle_response(response)
        except aiohttp.ClientError as e:
            msg = f"Request failed: {e}"
            raise APIError(msg) from e
