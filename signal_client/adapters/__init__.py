"""External-facing adapters (API clients, transport, storage)."""

from .api import base_client as api_base  # re-export namespace helpers
from .transport.websocket_client import WebSocketClient

__all__ = ["WebSocketClient", "api_base"]
