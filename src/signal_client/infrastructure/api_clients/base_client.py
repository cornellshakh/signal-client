from __future__ import annotations

import asyncio
import json
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
from signal_client.metrics import API_CLIENT_PERFORMANCE

if TYPE_CHECKING:
    from signal_client.services.circuit_breaker import CircuitBreaker
    from signal_client.services.rate_limiter import RateLimiter


HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_CONFLICT = 409
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVER_ERROR = 500

ERROR_CODE_MAP: dict[str, tuple[type[APIError], str | None]] = {
    "USER_NOT_GROUP_MEMBER": (
        ConflictError,
        "docs.signal-client.dev/errors#user-not-a-group-member",
    ),
    "USERNAME_ALREADY_TAKEN": (
        ConflictError,
        "docs.signal-client.dev/errors#username-already-taken",
    ),
    "GROUP_NOT_FOUND": (
        NotFoundError,
        "docs.signal-client.dev/errors#group-not-found",
    ),
    "ATTACHMENT_NOT_FOUND": (
        NotFoundError,
        "docs.signal-client.dev/errors#attachment-not-found",
    ),
    "CONTACT_NOT_FOUND": (
        NotFoundError,
        "docs.signal-client.dev/errors#contact-not-found",
    ),
    "RATE_LIMIT_EXCEEDED": (
        RateLimitError,
        "docs.signal-client.dev/errors#rate-limit-exceeded",
    ),
    "INTERNAL_SERVER_ERROR": (
        ServerError,
        "docs.signal-client.dev/errors#server-error",
    ),
}

ERROR_STATUS_MAP: dict[int, tuple[type[APIError], str]] = {
    HTTP_STATUS_UNAUTHORIZED: (
        AuthenticationError,
        "docs.signal-client.dev/errors#authentication-error",
    ),
    HTTP_STATUS_NOT_FOUND: (
        NotFoundError,
        "docs.signal-client.dev/errors#not-found-error",
    ),
    HTTP_STATUS_CONFLICT: (
        ConflictError,
        "docs.signal-client.dev/errors#conflict-error",
    ),
    HTTP_STATUS_TOO_MANY_REQUESTS: (
        RateLimitError,
        "docs.signal-client.dev/errors#rate-limit-error",
    ),
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
            payload, error_message = await self._extract_error_payload(response)
            normalized_code = self._normalize_error_code(payload)
            response_body = self._serialize_error_body(payload, error_message)
            error_text = error_message or normalized_code or f"HTTP {response.status}"
            self._raise_for_error(
                response.status, error_text, response_body, normalized_code
            )

        if response.content_type == "application/json":
            return await response.json()
        return await response.read()

    async def _extract_error_payload(
        self, response: aiohttp.ClientResponse
    ) -> tuple[object | None, str]:
        try:
            payload = await response.json()
        except aiohttp.ContentTypeError:
            text_payload = await response.text()
            return None, text_payload

        if isinstance(payload, dict):
            message = str(payload.get("error") or payload.get("message") or "")
            return payload, message
        if isinstance(payload, list):
            serialized = json.dumps(payload)
            return payload, serialized
        return payload, str(payload)

    @staticmethod
    def _normalize_error_code(payload: object | None) -> str | None:
        if isinstance(payload, dict):
            raw_code = payload.get("code")
            if isinstance(raw_code, str):
                return raw_code.strip().replace("-", "_").replace(" ", "_").upper()
        return None

    @staticmethod
    def _serialize_error_body(payload: object | None, fallback: str) -> str:
        if isinstance(payload, (dict, list)):
            return json.dumps(payload)
        return fallback

    def _raise_for_error(
        self,
        status: int,
        error_text: str,
        response_body: str,
        normalized_code: str | None,
    ) -> None:
        if normalized_code and normalized_code in ERROR_CODE_MAP:
            exc_cls, docs_url = ERROR_CODE_MAP[normalized_code]
            raise exc_cls(
                message=error_text,
                status_code=status,
                response_body=response_body,
                docs_url=docs_url,
            )

        if status in ERROR_STATUS_MAP:
            exc_cls, docs_url = ERROR_STATUS_MAP[status]
            raise exc_cls(
                message=error_text,
                status_code=status,
                response_body=response_body,
                docs_url=docs_url,
            )

        if status >= HTTP_STATUS_SERVER_ERROR:
            raise ServerError(
                message=error_text,
                status_code=status,
                response_body=response_body,
                docs_url="docs.signal-client.dev/errors#server-error",
            )

        raise APIError(
            message=error_text,
            status_code=status,
            response_body=response_body,
            docs_url="docs.signal-client.dev/errors#api-error",
        )

    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        url = f"{self._base_url}{path}"

        if self._rate_limiter:
            await self._rate_limiter.acquire()

        with API_CLIENT_PERFORMANCE.time():
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
        if last_exc:
            raise last_exc
        msg = f"Request failed after {self._retries} retries"
        raise APIError(msg)
