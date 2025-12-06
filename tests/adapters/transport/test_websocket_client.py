"""Tests for the WebSocketClient."""

from __future__ import annotations

import pytest

from signal_client.adapters.transport.websocket_client import WebSocketClient
from signal_client.observability.metrics import (
    WEBSOCKET_CONNECTION_STATE,
    WEBSOCKET_EVENTS,
)


@pytest.mark.parametrize(
    ("service_url", "expected"),
    [
        (
            "http://localhost:8080",
            "ws://localhost:8080/v1/receive/+123",
        ),
        (
            "https://example.com/api",
            "wss://example.com/api/v1/receive/+123",
        ),
        (
            "ws://signal.example.com",
            "ws://signal.example.com/v1/receive/+123",
        ),
        (
            "localhost:9000/base",
            "ws://localhost:9000/base/v1/receive/+123",
        ),
    ],
)
def test_websocket_uri_construction(service_url: str, expected: str) -> None:
    """Test WebSocket URI construction from various service URLs."""
    client = WebSocketClient(service_url, "+123")
    assert client._ws_uri == expected


def test_websocket_uri_invalid_scheme() -> None:
    """Test that an invalid scheme in the service URL raises a ValueError."""
    with pytest.raises(ValueError, match="Unsupported scheme"):
        WebSocketClient("ftp://example.com", "+123")


def test_websocket_metrics_markers() -> None:
    """Test that WebSocket metrics are updated correctly on connect/disconnect."""
    client = WebSocketClient("http://localhost:8080", "+123")

    connected_before = WEBSOCKET_EVENTS.labels(event="connected")._value.get()  # type: ignore[attr-defined]
    closed_before = WEBSOCKET_EVENTS.labels(event="closed")._value.get()  # type: ignore[attr-defined]

    assert WEBSOCKET_CONNECTION_STATE._value.get() == 0  # type: ignore[attr-defined]

    client._mark_connected()
    assert WEBSOCKET_CONNECTION_STATE._value.get() == 1  # type: ignore[attr-defined]
    assert (
        WEBSOCKET_EVENTS.labels(event="connected")._value.get()  # type: ignore[attr-defined]
        == connected_before + 1
    )

    client._mark_disconnected(reason="closed")
    assert WEBSOCKET_CONNECTION_STATE._value.get() == 0  # type: ignore[attr-defined]
    assert (
        WEBSOCKET_EVENTS.labels(event="closed")._value.get()  # type: ignore[attr-defined]
        == closed_before + 1
    )
