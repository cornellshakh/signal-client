from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

import aiohttp

from .config import Settings
from .context import Context
from .context_deps import ContextDependencies
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
from .infrastructure.api_clients.base_client import ClientConfig
from .infrastructure.schemas.message import Message
from .infrastructure.websocket_client import WebSocketClient
from .runtime.listener import BackpressurePolicy, MessageService
from .runtime.models import QueuedMessage
from .runtime.worker_pool import WorkerPool
from .services.circuit_breaker import CircuitBreaker
from .services.dead_letter_queue import DeadLetterQueue
from .services.lock_manager import LockManager
from .services.message_parser import MessageParser
from .services.rate_limiter import RateLimiter
from .storage.base import Storage
from .storage.redis import RedisStorage
from .storage.sqlite import SQLiteStorage


@dataclass
class APIClients:
    accounts: AccountsClient
    attachments: AttachmentsClient
    contacts: ContactsClient
    devices: DevicesClient
    general: GeneralClient
    groups: GroupsClient
    identities: IdentitiesClient
    messages: MessagesClient
    profiles: ProfilesClient
    reactions: ReactionsClient
    receipts: ReceiptsClient
    search: SearchClient
    sticker_packs: StickerPacksClient


class Application:
    """Explicit wiring of Signal client runtime components."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session: aiohttp.ClientSession | None = None
        self.rate_limiter = RateLimiter(
            rate_limit=settings.rate_limit, period=settings.rate_limit_period
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            reset_timeout=settings.circuit_breaker_reset_timeout,
            failure_rate_threshold=settings.circuit_breaker_failure_rate_threshold,
            min_requests_for_rate_calc=settings.circuit_breaker_min_requests_for_rate_calc,
        )

        self.storage = self._create_storage()
        self.api_clients: APIClients | None = None

        self.queue: asyncio.Queue[QueuedMessage] | None = None
        self.websocket_client: WebSocketClient | None = None
        self.dead_letter_queue: DeadLetterQueue | None = None
        self.message_parser = MessageParser()
        self.lock_manager = LockManager()
        self.context_dependencies: ContextDependencies | None = None
        self.context_factory: Callable[[Message], Context] | None = None
        self.message_service: MessageService | None = None
        self.worker_pool: WorkerPool | None = None

    async def initialize(self) -> None:
        if self.queue is not None:
            return

        self.session = aiohttp.ClientSession()
        self.api_clients = self._create_api_clients(self.session)

        self.queue = asyncio.Queue(maxsize=self.settings.queue_size)
        self.websocket_client = WebSocketClient(
            signal_service_url=self.settings.signal_service,
            phone_number=self.settings.phone_number,
        )
        self.dead_letter_queue = DeadLetterQueue(
            storage=self.storage,
            queue_name=self.settings.dlq_name,
            max_retries=self.settings.dlq_max_retries,
        )
        self.context_dependencies = ContextDependencies(
            accounts_client=self.api_clients.accounts,
            attachments_client=self.api_clients.attachments,
            contacts_client=self.api_clients.contacts,
            devices_client=self.api_clients.devices,
            general_client=self.api_clients.general,
            groups_client=self.api_clients.groups,
            identities_client=self.api_clients.identities,
            messages_client=self.api_clients.messages,
            profiles_client=self.api_clients.profiles,
            reactions_client=self.api_clients.reactions,
            receipts_client=self.api_clients.receipts,
            search_client=self.api_clients.search,
            sticker_packs_client=self.api_clients.sticker_packs,
            lock_manager=self.lock_manager,
            phone_number=self.settings.phone_number,
        )
        self.context_factory = partial(Context, dependencies=self.context_dependencies)
        self.message_service = MessageService(
            websocket_client=self.websocket_client,
            queue=self.queue,
            dead_letter_queue=self.dead_letter_queue,
            enqueue_timeout=self.settings.queue_put_timeout,
            backpressure_policy=(
                BackpressurePolicy.DROP_OLDEST
                if self.settings.queue_drop_oldest_on_timeout
                else BackpressurePolicy.FAIL_FAST
            ),
        )
        self.worker_pool = WorkerPool(
            context_factory=self.context_factory,
            queue=self.queue,
            message_parser=self.message_parser,
            pool_size=self.settings.worker_pool_size,
        )

    def _create_storage(self) -> Storage:
        if self.settings.storage_type.lower() == "redis":
            return RedisStorage(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
            )
        return SQLiteStorage(database=self.settings.sqlite_database)

    def _create_api_clients(self, session: aiohttp.ClientSession) -> APIClients:
        client_config = ClientConfig(
            session=session,
            base_url=self.settings.base_url,
            retries=self.settings.api_retries,
            backoff_factor=self.settings.api_backoff_factor,
            timeout=self.settings.api_timeout,
            rate_limiter=self.rate_limiter,
            circuit_breaker=self.circuit_breaker,
        )
        return APIClients(
            accounts=AccountsClient(client_config=client_config),
            attachments=AttachmentsClient(client_config=client_config),
            contacts=ContactsClient(client_config=client_config),
            devices=DevicesClient(client_config=client_config),
            general=GeneralClient(client_config=client_config),
            groups=GroupsClient(client_config=client_config),
            identities=IdentitiesClient(client_config=client_config),
            messages=MessagesClient(client_config=client_config),
            profiles=ProfilesClient(client_config=client_config),
            reactions=ReactionsClient(client_config=client_config),
            receipts=ReceiptsClient(client_config=client_config),
            search=SearchClient(client_config=client_config),
            sticker_packs=StickerPacksClient(client_config=client_config),
        )

    async def shutdown(self) -> None:
        if self.websocket_client is not None:
            await self.websocket_client.close()
        if self.session is not None:
            await self.session.close()
        close_storage = getattr(self.storage, "close", None)
        if close_storage is not None:
            await close_storage()
