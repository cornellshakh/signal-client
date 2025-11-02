from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import websockets


class WebSocketClient:
    def __init__(
        self,
        signal_service_url: str,
        phone_number: str,
    ) -> None:
        self._signal_service_url = signal_service_url
        self._phone_number = phone_number
        self._ws_uri = (
            f"ws://{self._signal_service_url}/v1/receive/{self._phone_number}"
        )
        self._stop = asyncio.Event()
        self._ws = None

    async def listen(self) -> AsyncGenerator[str, None]:
        """Listen for incoming messages and yield them."""
        while not self._stop.is_set():
            try:
                async with websockets.connect(self._ws_uri) as websocket:
                    self._ws = websocket
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
            except websockets.exceptions.ConnectionClosed:
                await asyncio.sleep(1)

    async def close(self) -> None:
        """Close the websocket connection."""
        self._stop.set()
        if self._ws:
            await self._ws.close()
