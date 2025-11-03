from __future__ import annotations

import asyncio
import json

import structlog

from signal_client.infrastructure.websocket_client import WebSocketClient
from signal_client.services.dead_letter_queue import DeadLetterQueue

log = structlog.get_logger()


class UnsupportedMessageError(Exception):
    """Custom exception for unsupported message types."""


class MessageService:
    def __init__(
        self,
        websocket_client: WebSocketClient,
        queue: asyncio.Queue[str],
        dead_letter_queue: DeadLetterQueue | None = None,
    ) -> None:
        self._websocket_client = websocket_client
        self._queue = queue
        self._dead_letter_queue = dead_letter_queue

    async def listen(self) -> None:
        """Listen for incoming messages and process them."""
        async for raw_message in self._websocket_client.listen():
            try:
                self._queue.put_nowait(raw_message)
            except asyncio.QueueFull:
                log.warning("Message queue is full, sending to DLQ")
                if self._dead_letter_queue:
                    await self._dead_letter_queue.send(json.loads(raw_message))
