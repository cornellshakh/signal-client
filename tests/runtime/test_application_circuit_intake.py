"""Tests for the application circuit intake."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from signal_client.app import Application
from signal_client.core.config import Settings
from signal_client.runtime.services.circuit_breaker import CircuitBreakerState


@pytest.mark.asyncio
async def test_application_pauses_intake_when_circuit_opens_then_closes():
    """Test that the application pauses intake when the circuit opens then closes."""
    settings = Settings.from_sources(
        config={
            "phone_number": "+15550000001",
            "signal_service": "http://localhost:8080",
            "base_url": "http://localhost:8080",
            "ingest_pause_seconds": 0.1,
            "circuit_breaker_reset_timeout": 1,
        }
    )
    app = Application(settings)
    await app.initialize()

    assert app.intake_controller is not None
    assert app._handle_circuit_state_change in app.circuit_breaker._state_listeners

    pause_mock: AsyncMock = AsyncMock()
    resume_mock: AsyncMock = AsyncMock()
    app.intake_controller.pause = pause_mock  # type: ignore[assignment]
    app.intake_controller.resume_now = resume_mock  # type: ignore[assignment]

    try:
        await app._handle_circuit_state_change("endpoint", CircuitBreakerState.OPEN)
        await app._handle_circuit_state_change("endpoint", CircuitBreakerState.CLOSED)
    finally:
        await app.shutdown()

    pause_mock.assert_awaited_once()
    resume_mock.assert_awaited_once()
    assert pause_mock.await_args.kwargs["reason"] == "circuit_open"
    assert pause_mock.await_args.kwargs["duration"] >= 1.0
    assert app._open_circuit_endpoints == set()
