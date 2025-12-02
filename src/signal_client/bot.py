from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import TYPE_CHECKING, Self

from .app import APIClients, Application
from .command import Command
from .compatibility import check_supported_versions
from .config import Settings
from .infrastructure.websocket_client import WebSocketClient
from .observability.logging import (
    ensure_structlog_configured,
    reset_structlog_configuration_guard,
)
from .runtime.listener import MessageService
from .runtime.models import QueuedMessage
from .runtime.worker_pool import WorkerPool

if TYPE_CHECKING:
    from .context import Context


class SignalClient:
    def __init__(
        self,
        config: dict | None = None,
        app: Application | None = None,
    ) -> None:
        check_supported_versions()
        settings = Settings.from_sources(config=config)

        self.app = app or Application(settings)
        self.settings = settings
        self._commands: list[Command] = []
        self._registered_command_ids: set[int] = set()
        self._middleware: list[
            Callable[[Context, Callable[[Context], Awaitable[None]]], Awaitable[None]]
        ] = []

        ensure_structlog_configured()

    def register(self, command: Command) -> None:
        """Register a new command."""
        self._commands.append(command)
        self._register_with_worker_pool(command)

    def use(
        self,
        middleware: Callable[
            [Context, Callable[[Context], Awaitable[None]]], Awaitable[None]
        ],
    ) -> None:
        """Register middleware to wrap command execution."""
        if middleware in self._middleware:
            return
        self._middleware.append(middleware)
        if self.app.worker_pool is not None:
            self.app.worker_pool.register_middleware(middleware)

    async def __aenter__(self) -> Self:
        await self.app.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.shutdown()

    async def start(self) -> None:
        """Start the bot."""
        await self.app.initialize()
        if self.app.worker_pool is None or self.app.message_service is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        worker_pool = self.app.worker_pool
        message_service = self.app.message_service

        for command in self._commands:
            self._register_with_worker_pool(command)

        for middleware in self._middleware:
            worker_pool.register_middleware(middleware)

        worker_pool.start()

        try:
            await asyncio.gather(
                message_service.listen(),
                worker_pool.join(),
            )
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown the bot gracefully."""
        # 1. Stop accepting new messages
        if self.app.websocket_client is not None:
            await self.app.websocket_client.close()

        # 2. Wait for the queue to be empty
        if self.app.queue is not None:
            await self.app.queue.join()

        # 3. Stop the workers
        if self.app.worker_pool is not None:
            self.app.worker_pool.stop()
            await self.app.worker_pool.join()

        # 4. Close the session and shutdown resources
        if self.app.session is not None:
            await self.app.session.close()
        close_storage = getattr(self.app.storage, "close", None)
        if close_storage is not None:
            await close_storage()

    def _register_with_worker_pool(self, command: Command) -> None:
        if id(command) in self._registered_command_ids:
            return

        if self.app.worker_pool is None:
            return

        self.app.worker_pool.register(command)
        self._registered_command_ids.add(id(command))

    @property
    def queue(self) -> asyncio.Queue[QueuedMessage]:
        if self.app.queue is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.queue

    @property
    def worker_pool(self) -> WorkerPool:
        if self.app.worker_pool is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.worker_pool

    @property
    def api_clients(self) -> APIClients:
        if self.app.api_clients is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.api_clients

    @property
    def websocket_client(self) -> WebSocketClient:
        if self.app.websocket_client is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.websocket_client

    @property
    def message_service(self) -> MessageService:
        if self.app.message_service is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.message_service

    async def set_websocket_client(self, websocket_client: WebSocketClient) -> None:
        """Override websocket client (test helper)."""
        await self.app.initialize()
        self.app.websocket_client = websocket_client
        if self.app.message_service is not None:
            self.app.message_service.set_websocket_client(websocket_client)


def reset_structlog_configuration_for_tests() -> None:
    """Reset structlog configuration guard. Intended for use in tests."""
    reset_structlog_configuration_guard()
