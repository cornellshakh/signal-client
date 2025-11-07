from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import TYPE_CHECKING, Self

import structlog

from .command import Command
from .compatibility import check_supported_versions
from .config import Settings
from .container import Container


class _StructlogConfigurator:
    _configured = False

    @classmethod
    def ensure_configured(cls) -> None:
        if cls._configured:
            return

        if getattr(structlog, "is_configured", None) and structlog.is_configured():
            cls._configured = True
            return

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ]
        )
        cls._configured = True

    @classmethod
    def reset(cls) -> None:
        cls._configured = False


if TYPE_CHECKING:
    from .context import Context


class SignalClient:
    def __init__(
        self,
        config: dict | None = None,
        container: Container | None = None,
    ) -> None:
        if container is None:
            container = Container()
        self.container = container
        self._commands: list[Command] = []
        self._registered_command_ids: set[int] = set()
        self._middleware: list[
            Callable[[Context, Callable[[Context], Awaitable[None]]], Awaitable[None]]
        ] = []

        check_supported_versions()
        settings = Settings.from_sources(config=config)
        self.container.settings.override(settings)

        _StructlogConfigurator.ensure_configured()

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
        worker_pool_manager = self.container.services_container.worker_pool_manager()
        worker_pool_manager.register_middleware(middleware)

    async def __aenter__(self) -> Self:
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
        message_service = self.container.services_container.message_service()
        worker_pool_manager = self.container.services_container.worker_pool_manager()

        for command in self._commands:
            self._register_with_worker_pool(command)

        for middleware in self._middleware:
            worker_pool_manager.register_middleware(middleware)

        worker_pool_manager.start()

        try:
            await asyncio.gather(
                message_service.listen(),
                worker_pool_manager.join(),
            )
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown the bot gracefully."""
        # 1. Stop accepting new messages
        websocket_client = self.container.services_container.websocket_client()
        await websocket_client.close()

        # 2. Wait for the queue to be empty
        queue = self.container.services_container.message_queue()
        await queue.join()

        # 3. Stop the workers
        worker_pool_manager = self.container.services_container.worker_pool_manager()
        worker_pool_manager.stop()
        await worker_pool_manager.join()

        # 4. Close the session and shutdown resources
        session = self.container.api_client_container.session()
        await session.close()
        self.container.shutdown_resources()

    def _register_with_worker_pool(self, command: Command) -> None:
        if id(command) in self._registered_command_ids:
            return

        worker_pool_manager = self.container.services_container.worker_pool_manager()
        worker_pool_manager.register(command)
        self._registered_command_ids.add(id(command))


def reset_structlog_configuration_for_tests() -> None:
    """Reset structlog configuration guard. Intended for use in tests."""
    _StructlogConfigurator.reset()
