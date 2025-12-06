"""Tests for the CircuitBreaker service."""

from __future__ import annotations

import asyncio

import pytest

from signal_client.observability.metrics import CIRCUIT_BREAKER_STATE
from signal_client.runtime.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)


@pytest.mark.asyncio
async def test_circuit_breaker_trips_after_failures(monkeypatch):
    """Test that the circuit breaker trips after a specified number of failures."""
    breaker = CircuitBreaker(
        failure_threshold=2,
        reset_timeout=1,
        failure_rate_threshold=0.5,
        min_requests_for_rate_calc=2,
    )

    async def failing_call():
        async with breaker.guard("endpoint"):
            raise RuntimeError("failure")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await failing_call()

    state = breaker._endpoint_states["endpoint"].state
    assert state == CircuitBreakerState.OPEN
    assert (
        CIRCUIT_BREAKER_STATE.labels(endpoint="endpoint", state="open")._value.get()  # type: ignore[attr-defined]
        == 1
    )

    with pytest.raises(ConnectionAbortedError):
        async with breaker.guard("endpoint"):
            pass

    await asyncio.sleep(1.1)

    async with breaker.guard("endpoint"):
        pass

    state = breaker._endpoint_states["endpoint"].state
    assert state == CircuitBreakerState.CLOSED
    assert (
        CIRCUIT_BREAKER_STATE.labels(endpoint="endpoint", state="closed")._value.get()  # type: ignore[attr-defined]
        == 1
    )


@pytest.mark.asyncio
async def test_circuit_breaker_notifies_state_listeners():
    """Test that the circuit breaker notifies registered state listeners."""
    breaker = CircuitBreaker(
        failure_threshold=1,
        reset_timeout=1,
        failure_rate_threshold=0.5,
        min_requests_for_rate_calc=1,
    )

    observed: list[tuple[str, CircuitBreakerState]] = []

    async def on_state_change(endpoint: str, state: CircuitBreakerState) -> None:
        observed.append((endpoint, state))

    breaker.register_state_listener(on_state_change)

    async def failing_call():
        async with breaker.guard("endpoint"):
            raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        await failing_call()

    await asyncio.sleep(1.1)

    async with breaker.guard("endpoint"):
        pass

    assert observed[:1] == [("endpoint", CircuitBreakerState.OPEN)]
    assert observed[-1] == ("endpoint", CircuitBreakerState.CLOSED)
