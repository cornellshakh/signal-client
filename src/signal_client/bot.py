from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

from .container import Container

if TYPE_CHECKING:
    from .command import Command


class SignalClient:
    def __init__(
        self,
        config: dict | None = None,
        container: Container | None = None,
    ) -> None:
        if container is None:
            container = Container()
        self.container = container
        if config is not None:
            self.container.config.from_dict(config)

        self._configure_logging()

    def _configure_logging(self) -> None:
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

    def register(self, command: Command) -> None:
        """Register a new command."""
        self.container.worker_pool_manager().register(command)

    async def start(self) -> None:
        """Start the bot."""
        message_service = self.container.message_service()
        worker_pool_manager = self.container.worker_pool_manager()
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
        websocket_client = self.container.websocket_client()
        await websocket_client.close()

        # 2. Wait for the queue to be empty
        queue = self.container.message_queue()
        await queue.join()

        # 3. Stop the workers
        worker_pool_manager = self.container.worker_pool_manager()
        worker_pool_manager.stop()
        await worker_pool_manager.join()

        # 4. Close the session and shutdown resources
        session = self.container.session()
        await session.close()
        self.container.shutdown_resources()
