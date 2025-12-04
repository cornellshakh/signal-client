from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Mapping

from yarl import URL

import aiohttp
import structlog

from signal_client.exceptions import (
    AuthenticationError,
    GroupNotFoundError,
    InvalidRecipientError,
    RateLimitError,
    ServerError,
    SignalAPIError,
)
from signal_client.observability.metrics import API_CLIENT_PERFORMANCE

if TYPE_CHECKING:
    from signal_client.services.circuit_breaker import CircuitBreaker
    from signal_client.services.rate_limiter import RateLimiter


HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_CONFLICT = 409
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVER_ERROR = 500


log = structlog.get_logger()


HeaderProvider = Callable[[str, str], Awaitable[Mapping[str, str]] | Mapping[str, str]]


@dataclass(slots=True)
class RequestOptions:
    """
    Optional parameters to customize a single API request.

    These options override the default client configuration for a specific request.

    Attributes:
        timeout: Request timeout in seconds.
        retries: Number of retries for this request.
        backoff_factor: Factor for exponential backoff between retries.
        idempotency_key: A unique key for idempotent requests.
        headers: Additional headers for this request.
    """

    timeout: float | None = None
    retries: int | None = None
    backoff_factor: float | None = None
    idempotency_key: str | None = None
    headers: Mapping[str, str] | None = None


@dataclass
class ClientConfig:
    """
    Configuration settings for an API client.

    Attributes:
        session: The aiohttp client session to use for requests.
        base_url: The base URL for the API endpoints.
        retries: Default number of retries for API requests.
        backoff_factor: Default backoff factor for retries.
        timeout: Default timeout in seconds for API requests.
        rate_limiter: An optional RateLimiter instance.
        circuit_breaker: An optional CircuitBreaker instance.
        default_headers: Default headers to send with all requests.
        header_provider: A callable to dynamically provide headers.
        endpoint_timeouts: A mapping of endpoint prefixes to specific timeouts.
        idempotency_header_name: The name of the header used for idempotency keys.
    """

    session: aiohttp.ClientSession
    base_url: str
    retries: int = 3
    backoff_factor: float = 0.5
    timeout: int = 30
    rate_limiter: RateLimiter | None = None
    circuit_breaker: CircuitBreaker | None = None
    default_headers: Mapping[str, str] | None = None
    header_provider: HeaderProvider | None = None
    endpoint_timeouts: Mapping[str, float] | None = None
    idempotency_header_name: str = "Idempotency-Key"


class BaseClient:
    """
    Base class for all Signal API clients.

    Provides common functionality for making HTTP requests, handling retries,
    timeouts, rate limiting, circuit breaking, and error responses.
    """

    def __init__(
        self,
        client_config: ClientConfig,
    ) -> None:
        """
        Initialize the BaseClient.

        Args:
            client_config: Configuration object for the client.
        """
        self._session = client_config.session
        self._base_url = client_config.base_url.rstrip("/")
        self._retries = client_config.retries
        self._backoff_factor = client_config.backoff_factor
        self._default_timeout_seconds = float(client_config.timeout)
        self._rate_limiter = client_config.rate_limiter
        self._circuit_breaker = client_config.circuit_breaker
        self._default_headers: dict[str, str] = (
            dict(client_config.default_headers) if client_config.default_headers else {}
        )
        self._header_provider = client_config.header_provider
        self._endpoint_timeouts: dict[str, float] = (
            {
                path: float(timeout)
                for path, timeout in (client_config.endpoint_timeouts or {}).items()
                if timeout is not None
            }
        )
        self._idempotency_header_name = client_config.idempotency_header_name

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        """
        Handle the API response, including error checking and JSON parsing.

        Args:
            response: The aiohttp ClientResponse object.

        Returns:
            Parsed JSON response, or raw bytes if content-type is not application/json.

        Raises:
            SignalAPIError: If the response indicates an error (status >= 400).
        """
        if response.status >= HTTP_STATUS_BAD_REQUEST:
            await self._raise_for_status(response)

        if response.content_type == "application/json":
            return await response.json()
        return await response.read()

    async def _raise_for_status(self, response: aiohttp.ClientResponse) -> None:
        """
        Raise a specific API exception based on the HTTP status code.

        Args:
            response: The aiohttp ClientResponse object.

        Raises:
            AuthenticationError: For 401 Unauthorized.
            RateLimitError: For 413/429 Too Many Requests.
            GroupNotFoundError: For 404 Not Found on group-related URLs.
            InvalidRecipientError: For 404 Not Found on other message send operations.
            ServerError: For 5xx server errors.
            SignalAPIError: For other API errors not specifically mapped.
        """
        if response.status == HTTP_STATUS_UNAUTHORIZED:
            raise AuthenticationError(
                f"Authentication failed: {response.reason}", status_code=response.status
            )
        if response.status in (HTTP_STATUS_TOO_MANY_REQUESTS, 413):
            raise RateLimitError(
                f"Rate limit exceeded: {response.reason}", status_code=response.status
            )
        if response.status == HTTP_STATUS_NOT_FOUND:
            if "group" in str(response.url).lower():
                raise GroupNotFoundError(
                    f"Group not found: {response.reason}", status_code=response.status
                )
            raise InvalidRecipientError(
                f"Invalid recipient: {response.reason}", status_code=response.status
            )
        if response.status >= HTTP_STATUS_SERVER_ERROR:
            raise ServerError(
                f"Server error: {response.reason}", status_code=response.status
            )

        try:
            error_body: dict[str, Any] | str
            if response.content_type == "application/json":
                error_body = await response.json()
            else:
                error_body = await response.text()

            if isinstance(error_body, dict):
                message = (
                    f"API Error: {response.status} {response.reason}\n"
                    f"{json.dumps(error_body)}"
                )
            else:
                message = f"API Error: {response.status} {response.reason}\n{error_body}"
        except (aiohttp.ClientError, json.JSONDecodeError):
            message = f"API Error: {response.status} {response.reason} (body unreadable)"
        raise SignalAPIError(message, status_code=response.status)

    async def _make_request(
        self,
        method: str,
        path: str,
        *,
        request_options: RequestOptions | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        """
        Make an HTTP request to the Signal API.

        This method handles URL construction, timeouts, retries, rate limiting,
        circuit breaking, and response processing.

        Args:
            method: The HTTP method (e.g., "GET", "POST").
            path: The API endpoint path (e.g., "/v1/messages").
            request_options: Optional RequestOptions to override client defaults.
            **kwargs: Additional keyword arguments passed to `aiohttp.ClientSession.request`.

        Returns:
            The parsed JSON response or raw bytes.

        Raises:
            SignalAPIError: If the request fails after all retries or due to an API error.
        """
        url = str(URL(self._base_url) / path.lstrip("/"))
        effective_timeout = self._resolve_timeout(path, request_options)
        retries = request_options.retries if request_options else None
        backoff_factor = request_options.backoff_factor if request_options else None
        headers = await self._headers_for_request(
            method=method,
            path=path,
            request_options=request_options,
            explicit_headers=kwargs.pop("headers", None),
        )
        if headers:
            kwargs["headers"] = headers

        if self._rate_limiter:
            await self._rate_limiter.acquire()

        with API_CLIENT_PERFORMANCE.time():
            if self._circuit_breaker:
                async with self._circuit_breaker.guard(path):
                    return await self._send_request_with_retries(
                        method,
                        url,
                        timeout_seconds=effective_timeout,
                        retries=retries,
                        backoff_factor=backoff_factor,
                        **kwargs,
                    )
            return await self._send_request_with_retries(
                method,
                url,
                timeout_seconds=effective_timeout,
                retries=retries,
                backoff_factor=backoff_factor,
                **kwargs,
            )

    async def _send_single_request(
        self,
        method: str,
        url: str,
        timeout_seconds: float,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes | Exception:
        """
        Send a single HTTP request.

        Args:
            method: HTTP method.
            url: Full URL for the request.
            timeout_seconds: Timeout for this single request.
            **kwargs: Additional arguments for `aiohttp.ClientSession.request`.

        Returns:
            The response content or an Exception if the request fails.
        """
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        try:
            async with self._session.request(
                method, url, timeout=timeout, **kwargs
            ) as response:
                return await self._handle_response(response)
        except (aiohttp.ClientError, ServerError, asyncio.TimeoutError) as e:
            return e

    async def _send_request_with_retries(
        self,
        method: str,
        url: str,
        *,
        timeout_seconds: float,
        retries: int | None = None,
        backoff_factor: float | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any] | list[dict[str, Any]] | bytes:
        """
        Send an HTTP request with retry logic.

        Args:
            method: HTTP method.
            url: Full URL for the request.
            timeout_seconds: Timeout for each single request attempt.
            retries: Number of retries. Overrides client default if provided.
            backoff_factor: Backoff factor. Overrides client default if provided.
            **kwargs: Additional arguments for `aiohttp.ClientSession.request`.

        Returns:
            The response content.

        Raises:
            Exception: The last encountered exception if all retries fail.
        """
        resolved_retries = self._retries if retries is None else retries
        resolved_backoff = (
            self._backoff_factor if backoff_factor is None else backoff_factor
        )
        last_exc: Exception | None = None
        for attempt in range(resolved_retries + 1):
            result = await self._send_single_request(
                method, url, timeout_seconds=timeout_seconds, **kwargs
            )
            if not isinstance(result, Exception):
                return result

            last_exc = result
            if attempt < resolved_retries:
                delay = resolved_backoff * (2**attempt)
                log.warning(
                    "api_client.retrying",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    max_retries=resolved_retries,
                    delay=delay,
                    exc_info=last_exc,
                )
                await asyncio.sleep(delay)
            else:
                log.exception(
                    "api_client.failed",
                    method=method,
                    url=url,
                    retries=resolved_retries,
                )
        if last_exc:
            raise last_exc
        msg = f"Request failed after {resolved_retries} retries"
        raise SignalAPIError(msg)

    async def _headers_for_request(
        self,
        *,
        method: str,
        path: str,
        request_options: RequestOptions | None,
        explicit_headers: Mapping[str, str] | None,
    ) -> dict[str, str]:
        """
        Assemble the headers for an outgoing request.

        Headers are gathered from default client headers, a dynamic header provider,
        and request-specific overrides.

        Args:
            method: HTTP method.
            path: API endpoint path.
            request_options: Request-specific options.
            explicit_headers: Headers explicitly provided for this call.

        Returns:
            A dictionary of headers to be sent with the request.
        """
        headers: dict[str, str] = dict(self._default_headers)

        if self._header_provider:
            provided = self._header_provider(method, path)
            if asyncio.iscoroutine(provided):
                provided = await provided
            if provided:
                headers.update(dict(provided))

        if explicit_headers:
            headers.update(dict(explicit_headers))

        if request_options and request_options.headers:
            headers.update(dict(request_options.headers))

        idempotency_key = (
            request_options.idempotency_key if request_options else None
        )
        if idempotency_key:
            headers[self._idempotency_header_name] = idempotency_key

        return headers

    def _resolve_timeout(
        self, path: str, request_options: RequestOptions | None
    ) -> float:
        """
        Resolve the effective timeout for a request.

        Resolution order: request_options > endpoint_timeouts > client_default.

        Args:
            path: The request path.
            request_options: Request-specific options.

        Returns:
            The resolved timeout value in seconds.
        """
        if request_options and request_options.timeout is not None:
            return float(request_options.timeout)

        for prefix, timeout in self._endpoint_timeouts.items():
            normalized_prefix = prefix.rstrip("/")
            if path.rstrip("/").startswith(normalized_prefix):
                return timeout

        return self._default_timeout_seconds
