from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

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

    def register(self, command: Command) -> None:
        """Register a new command."""
        self.container.worker_pool_manager().register(command)

    async def start(self) -> None:
        """Start the bot."""
        message_service = self.container.message_service()
        worker_pool_manager = self.container.worker_pool_manager()
        worker_pool_manager.start(self.container)

        try:
            await asyncio.gather(
                message_service.listen(),
                worker_pool_manager.join(),
            )
        finally:
            pass

    async def shutdown(self) -> None:
        """Shutdown the bot."""
        worker_pool_manager = self.container.worker_pool_manager()
        worker_pool_manager.stop()

        websocket_client = self.container.websocket_client()
        await websocket_client.close()

        self.container.shutdown_resources()
