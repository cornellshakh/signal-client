from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import aiohttp
import structlog

from signal_client.exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from signal_client.services.circuit_breaker import CircuitBreaker
    from signal_client.services.rate_limiter import RateLimiter


HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_CONFLICT = 409
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVER_ERROR = 500

ERROR_MESSAGE_MAP = {
    "User is not a group member": ConflictError,
    "Username already taken": ConflictError,
    "No group with that id found": NotFoundError,
    "No attachment with that name found": NotFoundError,
    "No contact with that id (...) found": NotFoundError,
    "Rate limit exceeded...": RateLimitError,
    "Couldn't get list of accounts...": ServerError,
    "Couldn't get list of attachments...": ServerError,
    "Couldn't detect MIME type for attachment": ServerError,
    "Couldn't serve attachment - please try again later": ServerError,
}

ERROR_DOCS_MAP = {
    "User is not a group member": (
        "docs.signal-client.dev/errors#user-not-a-group-member"
    ),
    "Username already taken": "docs.signal-client.dev/errors#username-already-taken",
    "No group with that id found": (
        "docs.signal-client.dev/errors#no-group-with-that-id-found"
    ),
    "No attachment with that name found": (
        "docs.signal-client.dev/errors#no-attachment-with-that-name-found"
    ),
    "No contact with that id (...) found": (
        "docs.signal-client.dev/errors#no-contact-with-that-id-found"
    ),
    "Rate limit exceeded...": "docs.signal-client.dev/errors#rate-limit-exceeded",
}


log = structlog.get_logger()


@dataclass
class ClientConfig:
    session: aiohttp.ClientSession
    base_url: str
    retries: int = 3
    backoff_factor: float = 0.5
    timeout: int = 30
    rate_limiter: RateLimiter | None = None
    circuit_breaker: CircuitBreaker | None = None


class BaseClient:
    def __init__(
        self,
        client_config: ClientConfig,
    ) -> None:
        self._session = client_config.session
        self._base_url = client_config.base_url
        self._retries = client_config.retries
        self._backoff_factor = client_config.backoff_factor
        self._timeout = aiohttp.ClientTimeout(total=client_config.timeout)
        self._rate_limiter = client_config.rate_limiter
        self._circuit_breaker = client_config.circuit_breaker

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        if response.status >= HTTP_STATUS_BAD_REQUEST:
            body = await response.text()
            for msg, exc in ERROR_MESSAGE_MAP.items():
                if msg in body:
                    docs_url = ERROR_DOCS_MAP.get(msg)
                    raise exc(
                        status_code=response.status,
                        response_body=body,
                        docs_url=docs_url,
                    )

            if response.status == HTTP_STATUS_UNAUTHORIZED:
                raise AuthenticationError(
                    status_code=response.status,
                    response_body=body,
                    docs_url="docs.signal-client.dev/errors#authentication-error",
                )
            if response.status == HTTP_STATUS_NOT_FOUND:
                raise NotFoundError(
                    status_code=response.status,
                    response_body=body,
                    docs_url="docs.signal-client.dev/errors#not-found-error",
                )
            if response.status == HTTP_STATUS_CONFLICT:
                raise ConflictError(
                    status_code=response.status,
                    response_body=body,
                    docs_url="docs.signal-client.dev/errors#conflict-error",
                )
            if response.status == HTTP_STATUS_TOO_MANY_REQUESTS:
                raise RateLimitError(
                    status_code=response.status,
                    response_body=body,
                    docs_url="docs.signal-client.dev/errors#rate-limit-error",
                )
            if response.status >= HTTP_STATUS_SERVER_ERROR:
                raise ServerError(
                    status_code=response.status,
                    response_body=body,
                    docs_url="docs.signal-client.dev/errors#server-error",
                )
            raise APIError(
                status_code=response.status,
                response_body=body,
                docs_url="docs.signal-client.dev/errors#api-error",
            )

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

        if self._rate_limiter:
            await self._rate_limiter.acquire()

        if self._circuit_breaker:
            async with self._circuit_breaker.guard(path):
                return await self._send_request_with_retries(method, url, **kwargs)
        return await self._send_request_with_retries(method, url, **kwargs)

    async def _send_single_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes | Exception:
        try:
            async with self._session.request(
                method, url, timeout=self._timeout, **kwargs
            ) as response:
                return await self._handle_response(response)
        except (aiohttp.ClientError, ServerError, asyncio.TimeoutError) as e:
            return e

    async def _send_request_with_retries(
        self,
        method: str,
        url: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        last_exc: Exception | None = None
        for attempt in range(self._retries + 1):
            result = await self._send_single_request(method, url, **kwargs)
            if not isinstance(result, Exception):
                return result

            last_exc = result
            if attempt < self._retries:
                delay = self._backoff_factor * (2**attempt)
                log.warning(
                    "Request failed, retrying...",
                    attempt=attempt + 1,
                    max_retries=self._retries,
                    delay=delay,
                    exc_info=last_exc,
                )
                await asyncio.sleep(delay)
            else:
                log.exception(
                    "Request failed after max retries",
                    attempt=attempt,
                )
        msg = f"Request failed after {self._retries} retries"
        raise APIError(msg) from last_exc
