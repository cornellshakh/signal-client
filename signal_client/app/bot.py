"""High-level Signal client wrapper for commands and worker orchestration."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import TYPE_CHECKING, Self

from signal_client.adapters.api.base_client import HeaderProvider
from signal_client.adapters.transport.websocket_client import WebSocketClient
from signal_client.app.application import APIClients, Application
from signal_client.core.command import Command
from signal_client.core.compatibility import check_supported_versions
from signal_client.core.config import Settings
from signal_client.observability.logging import (
    ensure_structlog_configured,
    reset_structlog_configuration_guard,
)
from signal_client.runtime.listener import MessageService
from signal_client.runtime.models import QueuedMessage
from signal_client.runtime.worker_pool import WorkerPool

if TYPE_CHECKING:
    from signal_client.core.context import Context


class SignalClient:
    """The main class for interacting with the Signal API and processing messages.

    This class orchestrates the various components of the signal-client,
    including API clients, message listeners, and worker pools.
    """

    def __init__(
        self,
        config: dict | None = None,
        app: Application | None = None,
        header_provider: HeaderProvider | None = None,
    ) -> None:
        """Initialize the SignalClient.

        Args:
            config: A dictionary of configuration overrides.
            app: An optional pre-initialized Application instance.
            header_provider: An optional callable or object that provides
                             additional HTTP headers for API requests.

        """
        check_supported_versions()
        settings = Settings.from_sources(config=config)

        ensure_structlog_configured(redaction_enabled=settings.log_redaction_enabled)
        self.app = app or Application(settings, header_provider=header_provider)
        self.settings = settings
        self._commands: list[Command] = []
        self._registered_command_ids: set[int] = set()
        self._middleware: list[
            Callable[[Context, Callable[[Context], Awaitable[None]]], Awaitable[None]]
        ] = []

    def register(self, command: Command) -> None:
        """Register a new command with the client.

        Registered commands will be executed when matching incoming messages.

        Args:
            command: The Command instance to register.

        """
        self._commands.append(command)
        self._register_with_worker_pool(command)

    def use(
        self,
        middleware: Callable[
            [Context, Callable[[Context], Awaitable[None]]], Awaitable[None]
        ],
    ) -> None:
        """Register middleware to wrap command execution.

        Middleware functions are called before command execution and can
        modify the context or prevent command execution.

        Args:
            middleware: The middleware callable to register.

        """
        if middleware in self._middleware:
            return
        self._middleware.append(middleware)
        if self.app.worker_pool is not None:
            self.app.worker_pool.register_middleware(middleware)

    async def __aenter__(self) -> Self:
        """Asynchronous context manager entry."""
        await self.app.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Asynchronous context manager exit.

        Ensures proper shutdown of the client.
        """
        await self.shutdown()

    async def start(self) -> None:
        """Start the SignalClient, including message listening and worker processing.

        This method will block indefinitely until the client is shut down.
        """
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
        """Shut down the SignalClient gracefully.

        This involves closing the websocket, waiting for queues to empty,
        stopping workers, and closing the aiohttp session.
        """
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
        """Register a command with the worker pool if not already present.

        Args:
            command: The command to register.

        """
        if id(command) in self._registered_command_ids:
            return

        if self.app.worker_pool is None:
            return

        self.app.worker_pool.register(command)
        self._registered_command_ids.add(id(command))

    @property
    def queue(self) -> asyncio.Queue[QueuedMessage]:
        """Get the message queue.

        Raises:
            RuntimeError: If the application is not initialized.

        Returns:
            The asyncio.Queue for messages.

        """
        if self.app.queue is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.queue

    @property
    def worker_pool(self) -> WorkerPool:
        """Get the worker pool.

        Raises:
            RuntimeError: If the application is not initialized.

        Returns:
            The WorkerPool instance.

        """
        if self.app.worker_pool is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.worker_pool

    @property
    def api_clients(self) -> APIClients:
        """Get the API clients.

        Raises:
            RuntimeError: If the application is not initialized.

        Returns:
            The APIClients instance.

        """
        if self.app.api_clients is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.api_clients

    @property
    def websocket_client(self) -> WebSocketClient:
        """Get the WebSocket client.

        Raises:
            RuntimeError: If the application is not initialized.

        Returns:
            The WebSocketClient instance.

        """
        if self.app.websocket_client is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.websocket_client

    @property
    def message_service(self) -> MessageService:
        """Get the message service.

        Raises:
            RuntimeError: If the application is not initialized.

        Returns:
            The MessageService instance.

        """
        if self.app.message_service is None:
            message = "Runtime not initialized. Call await app.initialize() first."
            raise RuntimeError(message)
        return self.app.message_service

    async def set_websocket_client(self, websocket_client: WebSocketClient) -> None:
        """Override the websocket client (primarily for testing purposes).

        Args:
            websocket_client: The new WebSocketClient instance to use.

        """
        await self.app.initialize()
        self.app.websocket_client = websocket_client
        if self.app.message_service is not None:
            self.app.message_service.set_websocket_client(websocket_client)


def reset_structlog_configuration_for_tests() -> None:
    """Reset structlog configuration guard. Intended for use in tests."""
    reset_structlog_configuration_guard()
