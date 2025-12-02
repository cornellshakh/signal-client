from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import structlog
import websockets
from websockets.exceptions import (
    ConnectionClosed,
    InvalidHandshake,
    InvalidURI,
)

log = structlog.get_logger()


class WebSocketClient:
    def __init__(
        self,
        signal_service_url: str,
        phone_number: str,
    ) -> None:
        self._signal_service_url = signal_service_url
        self._phone_number = phone_number
        self._ws_uri = self._build_ws_uri(signal_service_url, phone_number)
        self._stop = asyncio.Event()
        self._ws = None
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60

    async def listen(self) -> AsyncGenerator[str, None]:
        """Listen for incoming messages and yield them."""
        while not self._stop.is_set():
            try:
                async with websockets.connect(self._ws_uri) as websocket:
                    self._reconnect_delay = 1
                    self._ws = websocket  # type: ignore[assignment]
                    stop_task = asyncio.create_task(self._stop.wait())
                    while not self._stop.is_set():
                        recv_task = asyncio.create_task(websocket.recv())
                        done, _ = await asyncio.wait(
                            {recv_task, stop_task},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        if recv_task in done:
                            message = recv_task.result()
                            if isinstance(message, bytes):
                                yield message.decode("utf-8")
                            else:
                                yield str(message)
                        else:
                            recv_task.cancel()
                            break
            except asyncio.CancelledError:
                raise
            except ConnectionClosed:
                log.warning(
                    "websocket.closed_reconnecting",
                    delay=self._reconnect_delay,
                )
            except (OSError, InvalidURI, InvalidHandshake, asyncio.TimeoutError) as exc:
                log.warning(
                    "websocket.connection_error",
                    error=str(exc),
                    delay=self._reconnect_delay,
                )
            except Exception:
                log.exception(
                    "websocket.unexpected_error_reconnecting",
                    delay=self._reconnect_delay,
                )

            if self._stop.is_set():
                break

            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 2, self._max_reconnect_delay
            )

    async def close(self) -> None:
        """Close the websocket connection."""
        self._stop.set()
        if self._ws and self._ws.close_code is None:
            await self._ws.close()
            # Give the listen loop a moment to exit
            await asyncio.sleep(0)

    @staticmethod
    def _build_ws_uri(signal_service_url: str, phone_number: str) -> str:
        has_scheme = "://" in signal_service_url
        parsed = urlparse(
            signal_service_url if has_scheme else f"//{signal_service_url}",
            scheme="ws",
        )

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc
        path = parsed.path.rstrip("/")

        if scheme == "http":
            scheme = "ws"
        elif scheme == "https":
            scheme = "wss"
        elif scheme not in {"ws", "wss"}:
            error_msg = f"Unsupported scheme '{parsed.scheme}' for Signal service URL"
            raise ValueError(error_msg)

        if not netloc:
            error_msg = "Signal service URL must include a host"
            raise ValueError(error_msg)

        base_path = path if path.startswith("/") else f"/{path}" if path else ""
        ws_path = (
            f"{base_path}/v1/receive/{phone_number}"
            if base_path
            else f"/v1/receive/{phone_number}"
        )

        return urlunparse((scheme, netloc, ws_path, "", "", ""))
