import asyncio

import aiohttp
from dependency_injector import containers, providers

from .infrastructure.api_service import APIService
from .infrastructure.websocket_client import WebSocketClient
from .services.command_service import CommandService
from .services.message_service import MessageService
from .services.storage_service import StorageService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    message_queue = providers.Singleton(asyncio.Queue)

    session = providers.Singleton(aiohttp.ClientSession)

    api_service = providers.Singleton(
        APIService,
        session=session,
        signal_service=config.signal_service,
        phone_number=config.phone_number,
    )

    storage_service = providers.Singleton(
        StorageService,
        config=config.storage,
    )

    websocket_client = providers.Singleton(
        WebSocketClient,
        signal_service_url=config.signal_service,
        phone_number=config.phone_number,
    )

    message_service = providers.Singleton(
        MessageService,
        websocket_client=websocket_client,
        queue=message_queue,
    )

    command_service = providers.Singleton(
        CommandService,
        queue=message_queue,
        api_service=api_service,
        phone_number=config.phone_number,
    )
