from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiohttp
from dependency_injector import containers, providers

if TYPE_CHECKING:
    from .context import Context
    from .infrastructure.api_clients.base_client import ClientConfig

from .entities import ContextDependencies
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
from .infrastructure.storage.redis import RedisStorage
from .infrastructure.storage.sqlite import SQLiteStorage
from .infrastructure.websocket_client import WebSocketClient
from .services.circuit_breaker import CircuitBreaker
from .services.dead_letter_queue import DeadLetterQueue
from .services.lock_manager import LockManager
from .services.message_parser import MessageParser
from .services.message_service import MessageService
from .services.rate_limiter import RateLimiter
from .services.worker_pool_manager import WorkerPoolManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(
        default={
            "api_retries": 3,
            "api_backoff_factor": 0.5,
            "api_timeout": 30,
            "queue_size": 1000,
            "rate_limit": 50,
            "rate_limit_period": 1,
            "circuit_breaker_failure_threshold": 5,
            "circuit_breaker_reset_timeout": 30,
            "circuit_breaker_failure_rate_threshold": 0.5,
            "circuit_breaker_min_requests_for_rate_calc": 10,
            "storage_type": "sqlite",
            "redis_host": "localhost",
            "redis_port": 6379,
            "sqlite_database": "signal_client.db",
            "dlq_name": "signal_client_dlq",
        }
    )

    storage = providers.Selector(
        config.storage_type,
        sqlite=providers.Singleton(
            SQLiteStorage,
            database=config.sqlite_database,
        ),
        redis=providers.Singleton(
            RedisStorage,
            host=config.redis_host,
            port=config.redis_port,
        ),
    )

    circuit_breaker = providers.Singleton(
        CircuitBreaker,
        failure_threshold=config.circuit_breaker_failure_threshold,
        reset_timeout=config.circuit_breaker_reset_timeout,
        failure_rate_threshold=config.circuit_breaker_failure_rate_threshold,
        min_requests_for_rate_calc=config.circuit_breaker_min_requests_for_rate_calc,
    )

    rate_limiter = providers.Singleton(
        RateLimiter,
        rate_limit=config.rate_limit,
        period=config.rate_limit_period,
    )

    message_queue: providers.Singleton[asyncio.Queue[str]] = providers.Singleton(
        asyncio.Queue,
        maxsize=config.queue_size,
    )

    session = providers.Singleton(aiohttp.ClientSession)

    client_config: providers.Factory[ClientConfig] = providers.Factory(
        "signal_client.infrastructure.api_clients.base_client.ClientConfig",
        session=session,
        base_url=config.base_url,
        retries=config.api_retries,
        backoff_factor=config.api_backoff_factor,
        timeout=config.api_timeout,
        rate_limiter=rate_limiter,
        circuit_breaker=circuit_breaker,
    )

    accounts_client = providers.Singleton(AccountsClient, client_config=client_config)
    attachments_client = providers.Singleton(
        AttachmentsClient, client_config=client_config
    )
    contacts_client = providers.Singleton(ContactsClient, client_config=client_config)
    devices_client = providers.Singleton(DevicesClient, client_config=client_config)
    general_client = providers.Singleton(GeneralClient, client_config=client_config)
    groups_client = providers.Singleton(GroupsClient, client_config=client_config)
    identities_client = providers.Singleton(
        IdentitiesClient, client_config=client_config
    )
    messages_client = providers.Singleton(MessagesClient, client_config=client_config)
    profiles_client = providers.Singleton(ProfilesClient, client_config=client_config)
    reactions_client = providers.Singleton(ReactionsClient, client_config=client_config)
    receipts_client = providers.Singleton(ReceiptsClient, client_config=client_config)
    search_client = providers.Singleton(SearchClient, client_config=client_config)
    sticker_packs_client = providers.Singleton(
        StickerPacksClient, client_config=client_config
    )

    websocket_client = providers.Singleton(
        WebSocketClient,
        signal_service_url=config.signal_service,
        phone_number=config.phone_number,
    )

    dead_letter_queue = providers.Singleton(
        DeadLetterQueue,
        storage=storage,
        queue_name=config.dlq_name,
    )

    message_service = providers.Singleton(
        MessageService,
        websocket_client=websocket_client,
        queue=message_queue,
        dead_letter_queue=dead_letter_queue,
    )

    message_parser = providers.Singleton(MessageParser)

    lock_manager = providers.Singleton(LockManager)

    context_dependencies = providers.Factory(
        ContextDependencies,
        accounts_client=accounts_client,
        attachments_client=attachments_client,
        contacts_client=contacts_client,
        devices_client=devices_client,
        general_client=general_client,
        groups_client=groups_client,
        identities_client=identities_client,
        messages_client=messages_client,
        profiles_client=profiles_client,
        reactions_client=reactions_client,
        receipts_client=receipts_client,
        search_client=search_client,
        sticker_packs_client=sticker_packs_client,
        lock_manager=lock_manager,
        phone_number=config.phone_number,
    )

    context: providers.Factory[Context] = providers.Factory(
        "signal_client.context.Context",
        dependencies=context_dependencies,
    )

    worker_pool_manager = providers.Singleton(
        WorkerPoolManager,
        context_factory=context.provider,
        queue=message_queue,
        message_parser=message_parser,
        pool_size=config.worker_pool_size,
    )
