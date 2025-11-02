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
        command_service = self.container.command_service()
        command_service.register(command)

    async def start(self) -> None:
        """Start the bot."""
        message_service = self.container.message_service()
        command_service = self.container.command_service()
        api_service = self.container.api_service()

        try:
            await asyncio.gather(
                message_service.listen(),
                command_service.process_messages(),
            )
        finally:
            await api_service.close()

    async def shutdown(self) -> None:
        """Shutdown the bot."""
        command_service = self.container.command_service()
        command_service.stop()

        websocket_client = self.container.websocket_client()
        await websocket_client.close()

        api_service = self.container.api_service()
        await api_service.close()
