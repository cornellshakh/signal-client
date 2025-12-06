"""Circuit breaker implementation for API clients."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

import structlog

from signal_client.observability.metrics import CIRCUIT_BREAKER_STATE

log = structlog.get_logger()


class CircuitBreakerState(Enum):
    """Represents the possible states of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


StateChangeListener = Callable[[str, CircuitBreakerState], Awaitable[None] | None]


@dataclass
class EndpointState:
    """Represents the state of a specific endpoint within the circuit breaker."""

    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failures: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    successes: int = 0
    requests: int = 0


class CircuitBreaker:
    """Simple circuit breaker with counts, failure rate threshold, and timed resets."""

    def __init__(
        self,
        failure_threshold: int,
        reset_timeout: int,
        failure_rate_threshold: float = 0.5,
        min_requests_for_rate_calc: int = 10,
    ) -> None:
        """Initialize a CircuitBreaker instance.

        Args:
            failure_threshold: Consecutive failures before opening the circuit.
            reset_timeout: Seconds to wait before transitioning from OPEN to HALF_OPEN.
            failure_rate_threshold: Failure rate proportion to open the circuit.
            min_requests_for_rate_calc: Minimum requests for failure rate calculation.

        """
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._failure_rate_threshold = failure_rate_threshold
        self._min_requests_for_rate_calc = min_requests_for_rate_calc
        self._endpoint_states: dict[str, EndpointState] = {}
        self._state_listeners: set[StateChangeListener] = set()

    def register_state_listener(self, listener: StateChangeListener) -> None:
        """Register a callback invoked on state transitions."""
        self._state_listeners.add(listener)

    @asynccontextmanager
    async def guard(self, endpoint_key: str) -> AsyncGenerator[None, None]:
        """Yield if allowed; trip on consecutive or rate-based failures."""
        endpoint_state = self._endpoint_states.setdefault(endpoint_key, EndpointState())
        self._record_state(endpoint_key, endpoint_state.state)

        if endpoint_state.state == CircuitBreakerState.OPEN:
            if (
                time.monotonic() - endpoint_state.last_failure_time
                > self._reset_timeout
            ):
                await self._set_state(
                    endpoint_key, endpoint_state, CircuitBreakerState.HALF_OPEN
                )
                log.info("Circuit breaker is now half-open.", endpoint=endpoint_key)
            else:
                msg = f"Circuit breaker is open for endpoint: {endpoint_key}."
                raise ConnectionAbortedError(msg)

        endpoint_state.requests += 1
        try:
            yield
        except Exception:
            endpoint_state.failures += 1
            endpoint_state.consecutive_failures += 1
            if (
                endpoint_state.state == CircuitBreakerState.HALF_OPEN
                or endpoint_state.consecutive_failures >= self._failure_threshold
                or (
                    endpoint_state.requests >= self._min_requests_for_rate_calc
                    and (endpoint_state.failures / endpoint_state.requests)
                    >= self._failure_rate_threshold
                )
            ):
                await self._trip(endpoint_key, endpoint_state)
            raise
        else:
            endpoint_state.successes += 1
            endpoint_state.consecutive_failures = 0
            if endpoint_state.state == CircuitBreakerState.HALF_OPEN:
                await self._reset(endpoint_key, endpoint_state)

    async def _trip(self, endpoint_key: str, endpoint_state: EndpointState) -> None:
        endpoint_state.last_failure_time = time.monotonic()
        endpoint_state.failures = 0
        endpoint_state.consecutive_failures = 0
        endpoint_state.successes = 0
        endpoint_state.requests = 0
        await self._set_state(endpoint_key, endpoint_state, CircuitBreakerState.OPEN)
        log.warning(
            "Circuit breaker has been tripped and is now open.",
            endpoint=endpoint_key,
        )

    async def _reset(self, endpoint_key: str, endpoint_state: EndpointState) -> None:
        endpoint_state.failures = 0
        endpoint_state.consecutive_failures = 0
        endpoint_state.successes = 0
        endpoint_state.requests = 0
        await self._set_state(endpoint_key, endpoint_state, CircuitBreakerState.CLOSED)
        log.info(
            "Circuit breaker has been reset and is now closed.",
            endpoint=endpoint_key,
        )

    def _record_state(self, endpoint_key: str, state: CircuitBreakerState) -> None:
        for candidate in CircuitBreakerState:
            value = 1 if candidate == state else 0
            CIRCUIT_BREAKER_STATE.labels(
                endpoint=endpoint_key,
                state=candidate.value,
            ).set(value)

    async def _set_state(
        self,
        endpoint_key: str,
        endpoint_state: EndpointState,
        new_state: CircuitBreakerState,
    ) -> None:
        if endpoint_state.state is not new_state:
            endpoint_state.state = new_state
            await self._notify_state_change(endpoint_key, new_state)
        self._record_state(endpoint_key, new_state)

    async def _notify_state_change(
        self, endpoint_key: str, state: CircuitBreakerState
    ) -> None:
        for listener in tuple(self._state_listeners):
            try:
                result = listener(endpoint_key, state)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001, PERF203
                log.warning(
                    "circuit_breaker.listener_failed",
                    endpoint=endpoint_key,
                    state=state.value,
                    exc_info=True,
                    error=exc,
                )
