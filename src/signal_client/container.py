from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiohttp
from dependency_injector import containers, providers

if TYPE_CHECKING:
    from .context import Context
    from .infrastructure.api_clients.base_client import ClientConfig

from .config import Settings
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
from .services.models import QueuedMessage
from .services.rate_limiter import RateLimiter
from .services.worker_pool_manager import WorkerPoolManager


class StorageContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    storage = providers.Selector(
        settings.provided.storage_type,
        sqlite=providers.Singleton(
            SQLiteStorage,
            database=settings.provided.sqlite_database,
        ),
        redis=providers.Singleton(
            RedisStorage,
            host=settings.provided.redis_host,
            port=settings.provided.redis_port,
        ),
    )


class APIClientContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)
    circuit_breaker = providers.Dependency(instance_of=CircuitBreaker)
    rate_limiter = providers.Dependency(instance_of=RateLimiter)

    session = providers.Singleton(aiohttp.ClientSession)

    client_config: providers.Factory[ClientConfig] = providers.Factory(
        "signal_client.infrastructure.api_clients.base_client.ClientConfig",
        session=session,
        base_url=settings.provided.base_url,
        retries=settings.provided.api_retries,
        backoff_factor=settings.provided.api_backoff_factor,
        timeout=settings.provided.api_timeout,
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


class ServicesContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)
    storage_container = providers.DependenciesContainer()
    api_client_container = providers.DependenciesContainer()

    message_queue: providers.Singleton[asyncio.Queue[QueuedMessage]] = (
        providers.Singleton(
            asyncio.Queue,
            maxsize=settings.provided.queue_size,
        )
    )

    websocket_client = providers.Singleton(
        WebSocketClient,
        signal_service_url=settings.provided.signal_service,
        phone_number=settings.provided.phone_number,
    )

    dead_letter_queue = providers.Singleton(
        DeadLetterQueue,
        storage=storage_container.storage,
        queue_name=settings.provided.dlq_name,
        max_retries=settings.provided.dlq_max_retries,
    )

    message_service = providers.Singleton(
        MessageService,
        websocket_client=websocket_client,
        queue=message_queue,
        dead_letter_queue=dead_letter_queue,
        enqueue_timeout=settings.provided.queue_put_timeout,
        drop_oldest_on_timeout=settings.provided.queue_drop_oldest_on_timeout,
    )

    message_parser = providers.Singleton(MessageParser)

    lock_manager = providers.Singleton(LockManager)

    context_dependencies = providers.Factory(
        ContextDependencies,
        accounts_client=api_client_container.accounts_client,
        attachments_client=api_client_container.attachments_client,
        contacts_client=api_client_container.contacts_client,
        devices_client=api_client_container.devices_client,
        general_client=api_client_container.general_client,
        groups_client=api_client_container.groups_client,
        identities_client=api_client_container.identities_client,
        messages_client=api_client_container.messages_client,
        profiles_client=api_client_container.profiles_client,
        reactions_client=api_client_container.reactions_client,
        receipts_client=api_client_container.receipts_client,
        search_client=api_client_container.search_client,
        sticker_packs_client=api_client_container.sticker_packs_client,
        lock_manager=lock_manager,
        phone_number=settings.provided.phone_number,
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
        pool_size=settings.provided.worker_pool_size,
    )


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)

    circuit_breaker = providers.Singleton(
        CircuitBreaker,
        failure_threshold=settings.provided.circuit_breaker_failure_threshold,
        reset_timeout=settings.provided.circuit_breaker_reset_timeout,
        failure_rate_threshold=settings.provided.circuit_breaker_failure_rate_threshold,
        min_requests_for_rate_calc=settings.provided.circuit_breaker_min_requests_for_rate_calc,
    )

    rate_limiter = providers.Singleton(
        RateLimiter,
        rate_limit=settings.provided.rate_limit,
        period=settings.provided.rate_limit_period,
    )

    storage_container: providers.Container[StorageContainer] = providers.Container(
        StorageContainer,
        settings=settings,
    )

    api_client_container: providers.Container[APIClientContainer] = providers.Container(
        APIClientContainer,
        settings=settings,
        circuit_breaker=circuit_breaker,
        rate_limiter=rate_limiter,
    )

    services_container: providers.Container[ServicesContainer] = providers.Container(
        ServicesContainer,
        settings=settings,
        storage_container=storage_container,
        api_client_container=api_client_container,
    )
