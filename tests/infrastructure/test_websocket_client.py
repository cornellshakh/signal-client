from __future__ import annotations

import pytest

from signal_client.infrastructure.websocket_client import WebSocketClient


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
    client = WebSocketClient(service_url, "+123")
    assert client._ws_uri == expected


def test_websocket_uri_invalid_scheme() -> None:
    with pytest.raises(ValueError, match="Unsupported scheme"):
        WebSocketClient("ftp://example.com", "+123")
