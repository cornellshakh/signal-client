import asyncio

import aiohttp
from dependency_injector import containers, providers

from .infrastructure.api_clients import (
    AccountsClient,
    AttachmentsClient,
    ContactsClient,
    DevicesClient,
    GeneralClient,
    GroupsClient,
    IdentitiesClient,
    MessagesClient,
    ProfilesClient,
    ReactionsClient,
    ReceiptsClient,
    SearchClient,
    StickerPacksClient,
)
from .infrastructure.websocket_client import WebSocketClient
from .services.lock_manager import LockManager
from .services.message_parser import MessageParser
from .services.message_service import MessageService
from .services.storage_service import StorageService
from .services.worker_pool_manager import WorkerPoolManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    message_queue: providers.Singleton[asyncio.Queue[str]] = providers.Singleton(
        asyncio.Queue
    )

    session = providers.Resource(aiohttp.ClientSession)

    accounts_client = providers.Singleton(
        AccountsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    attachments_client = providers.Singleton(
        AttachmentsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    contacts_client = providers.Singleton(
        ContactsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    devices_client = providers.Singleton(
        DevicesClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    general_client = providers.Singleton(
        GeneralClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    groups_client = providers.Singleton(
        GroupsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    identities_client = providers.Singleton(
        IdentitiesClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    messages_client = providers.Singleton(
        MessagesClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    profiles_client = providers.Singleton(
        ProfilesClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    reactions_client = providers.Singleton(
        ReactionsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    receipts_client = providers.Singleton(
        ReceiptsClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    search_client = providers.Singleton(
        SearchClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
    )
    sticker_packs_client = providers.Singleton(
        StickerPacksClient,
        session=session,
        base_url=config.base_url,
        auth_token=config.auth_token,
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

    lock_manager = providers.Singleton(LockManager)

    message_parser = providers.Singleton(MessageParser)

    worker_pool_manager = providers.Singleton(
        WorkerPoolManager,
        queue=message_queue,
        message_parser=message_parser,
        pool_size=config.worker_pool_size,
    )
