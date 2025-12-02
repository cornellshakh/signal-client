from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

import structlog

from signal_client.observability.metrics import CIRCUIT_BREAKER_STATE

log = structlog.get_logger()


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


@dataclass
class EndpointState:
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
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._failure_rate_threshold = failure_rate_threshold
        self._min_requests_for_rate_calc = min_requests_for_rate_calc
        self._endpoint_states: dict[str, EndpointState] = {}

    @asynccontextmanager
    async def guard(self, endpoint_key: str) -> AsyncGenerator[None, None]:
        """Yield if allowed; trip when consecutive or rate-based failure thresholds are exceeded."""
        endpoint_state = self._endpoint_states.setdefault(endpoint_key, EndpointState())
        self._record_state(endpoint_key, endpoint_state.state)

        if endpoint_state.state == CircuitBreakerState.OPEN:
            if (
                time.monotonic() - endpoint_state.last_failure_time
                > self._reset_timeout
            ):
                endpoint_state.state = CircuitBreakerState.HALF_OPEN
                log.info("Circuit breaker is now half-open.", endpoint=endpoint_key)
                self._record_state(endpoint_key, endpoint_state.state)
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
                self._trip(endpoint_key, endpoint_state)
            raise
        else:
            endpoint_state.successes += 1
            endpoint_state.consecutive_failures = 0
            if endpoint_state.state == CircuitBreakerState.HALF_OPEN:
                self._reset(endpoint_key, endpoint_state)

    def _trip(self, endpoint_key: str, endpoint_state: EndpointState) -> None:
        endpoint_state.state = CircuitBreakerState.OPEN
        endpoint_state.last_failure_time = time.monotonic()
        endpoint_state.failures = 0
        endpoint_state.consecutive_failures = 0
        endpoint_state.successes = 0
        endpoint_state.requests = 0
        log.warning(
            "Circuit breaker has been tripped and is now open.", endpoint=endpoint_key
        )
        self._record_state(endpoint_key, endpoint_state.state)

    def _reset(self, endpoint_key: str, endpoint_state: EndpointState) -> None:
        endpoint_state.state = CircuitBreakerState.CLOSED
        endpoint_state.failures = 0
        endpoint_state.consecutive_failures = 0
        endpoint_state.successes = 0
        endpoint_state.requests = 0
        log.info(
            "Circuit breaker has been reset and is now closed.", endpoint=endpoint_key
        )
        self._record_state(endpoint_key, endpoint_state.state)

    def _record_state(self, endpoint_key: str, state: CircuitBreakerState) -> None:
        for candidate in CircuitBreakerState:
            value = 1 if candidate == state else 0
            CIRCUIT_BREAKER_STATE.labels(
                endpoint=endpoint_key,
                state=candidate.value,
            ).set(value)
