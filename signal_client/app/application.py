"""Application wiring for the Signal client runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

import aiohttp
import structlog

from signal_client.adapters.api import (
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
from signal_client.adapters.api.base_client import ClientConfig, HeaderProvider
from signal_client.adapters.api.schemas.message import Message
from signal_client.adapters.storage.base import Storage
from signal_client.adapters.storage.memory import MemoryStorage
from signal_client.adapters.storage.redis import RedisStorage
from signal_client.adapters.storage.sqlite import SQLiteStorage
from signal_client.adapters.transport.websocket_client import WebSocketClient
from signal_client.core.config import Settings
from signal_client.core.context import Context
from signal_client.core.context_deps import ContextDependencies
from signal_client.observability.logging import ensure_structlog_configured, safe_log
from signal_client.runtime.listener import BackpressurePolicy, MessageService
from signal_client.runtime.models import QueuedMessage
from signal_client.runtime.services.checkpoint_store import IngestCheckpointStore
from signal_client.runtime.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)
from signal_client.runtime.services.dead_letter_queue import DeadLetterQueue
from signal_client.runtime.services.intake_controller import IntakeController
from signal_client.runtime.services.lock_manager import LockManager
from signal_client.runtime.services.message_parser import MessageParser
from signal_client.runtime.services.persistent_queue import PersistentQueue
from signal_client.runtime.services.rate_limiter import RateLimiter
from signal_client.runtime.worker_pool import WorkerPool

log = structlog.get_logger()


@dataclass
class APIClients:
    """A container for all the API clients.

    Attributes:
        accounts: Client for accounts API.
        attachments: Client for attachments API.
        contacts: Client for contacts API.
        devices: Client for devices API.
        general: Client for general API.
        groups: Client for groups API.
        identities: Client for identities API.
        messages: Client for messages API.
        profiles: Client for profiles API.
        reactions: Client for reactions API.
        receipts: Client for receipts API.
        search: Client for search API.
        sticker_packs: Client for sticker packs API.

    """

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
    """Explicit wiring of Signal client runtime components.

    This class is responsible for initializing and managing the lifecycle
    of all components within the Signal client, including API clients,
    storage, message queues, and worker pools.
    """

    def __init__(
        self, settings: Settings, *, header_provider: HeaderProvider | None = None
    ) -> None:
        """Initialize the Application instance.

        Args:
            settings: The application settings.
            header_provider: An optional callable or object that provides
                             additional HTTP headers for API requests.

        """
        ensure_structlog_configured(redaction_enabled=settings.log_redaction_enabled)
        self._log = structlog.get_logger()
        self.settings = settings
        self._header_provider = header_provider
        self.session: aiohttp.ClientSession | None = None
        self.rate_limiter = RateLimiter(
            rate_limit=settings.rate_limit, period=settings.rate_limit_period
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            reset_timeout=settings.circuit_breaker_reset_timeout,
            failure_rate_threshold=settings.circuit_breaker_failure_rate_threshold,
            min_requests_for_rate_calc=(
                settings.circuit_breaker_min_requests_for_rate_calc
            ),
        )

        self.storage = self._create_storage()
        if isinstance(self.storage, MemoryStorage):
            self._log_warning(
                "Using transient in-memory storage. No data will be persisted.",
                event_slug="storage.in_memory.active",
            )

        self.api_clients: APIClients | None = None

        self.queue: asyncio.Queue[QueuedMessage] | None = None
        self.websocket_client: WebSocketClient | None = None
        self.dead_letter_queue: DeadLetterQueue | None = None
        self.persistent_queue: PersistentQueue | None = None
        self.ingest_checkpoint_store: IngestCheckpointStore | None = None
        self.intake_controller: IntakeController | None = None
        self.message_parser = MessageParser()
        self.lock_manager: LockManager | None = None
        self.context_dependencies: ContextDependencies | None = None
        self.context_factory: Callable[[Message], Context] | None = None
        self.message_service: MessageService | None = None
        self.worker_pool: WorkerPool | None = None
        self._circuit_state_lock: asyncio.Lock | None = None
        self._open_circuit_endpoints: set[str] = set()

    def _log_warning(self, message: str, **kwargs: object) -> None:
        """Emit a warning, tolerating minimal structlog configurations.

        Falls back to stdlib logging if the current structlog logger does not
        accept keyword arguments (e.g., when using PrintLogger).
        """
        safe_log(self._log, "warning", message, **kwargs)

    async def initialize(self) -> None:
        """Initialize all components of the application.

        This method sets up the AIOHTTP client session, API clients,
        message queues, storage, and worker pools. It must be called
        before the application can start processing messages.
        """
        if self.queue is not None:
            return

        self.session = aiohttp.ClientSession()
        self.api_clients = self._create_api_clients(self.session)

        self.queue = asyncio.Queue(maxsize=self.settings.queue_size)
        if self.settings.durable_queue_enabled:
            self.persistent_queue = PersistentQueue(
                storage=self.storage,
                key=self.settings.ingest_queue_name,
                max_length=self.settings.durable_queue_max_length,
            )
        self.ingest_checkpoint_store = IngestCheckpointStore(
            storage=self.storage,
            key=self.settings.ingest_checkpoint_key,
            window_size=self.settings.ingest_checkpoint_window,
        )
        self.intake_controller = IntakeController(
            default_pause_seconds=self.settings.ingest_pause_seconds
        )
        self.rate_limiter.set_wait_listener(self._handle_rate_limit_wait)
        self._circuit_state_lock = asyncio.Lock()
        self.websocket_client = WebSocketClient(
            signal_service_url=self.settings.signal_service,
            phone_number=self.settings.phone_number,
            websocket_path=self.settings.websocket_path,
        )
        redis_client = (
            self.storage.client
            if self.settings.distributed_locks_enabled
            and isinstance(self.storage, RedisStorage)
            else None
        )
        self.lock_manager = LockManager(
            redis_client=redis_client,
            lock_timeout_seconds=self.settings.distributed_lock_timeout,
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
            settings=self.settings,
        )
        self.context_factory = partial(Context, dependencies=self.context_dependencies)
        self.message_service = MessageService(
            websocket_client=self.websocket_client,
            queue=self.queue,
            dead_letter_queue=self.dead_letter_queue,
            persistent_queue=self.persistent_queue,
            intake_controller=self.intake_controller,
            enqueue_timeout=self.settings.queue_put_timeout,
            backpressure_policy=(
                BackpressurePolicy.DROP_OLDEST
                if self.settings.queue_drop_oldest_on_timeout
                else BackpressurePolicy.FAIL_FAST
            ),
        )
        self.circuit_breaker.register_state_listener(self._handle_circuit_state_change)
        self.worker_pool = WorkerPool(
            context_factory=self.context_factory,
            queue=self.queue,
            message_parser=self.message_parser,
            dead_letter_queue=self.dead_letter_queue,
            checkpoint_store=self.ingest_checkpoint_store,
            pool_size=self.settings.worker_pool_size,
            shard_count=self.settings.worker_shard_count,
            lock_manager=self.lock_manager,
        )
        if self.persistent_queue:
            replay = await self.persistent_queue.replay()
            for item in replay:
                queued = QueuedMessage(raw=item.raw, enqueued_at=item.enqueued_at)
                try:
                    self.queue.put_nowait(queued)
                except asyncio.QueueFull:
                    self._log_warning(
                        "persistent_queue.replay_dropped",
                        reason="queue_full",
                        queue_depth=self.queue.qsize(),
                        queue_maxsize=self.queue.maxsize,
                    )
                    break

    def _create_storage(self) -> Storage:
        """Create and return the appropriate storage backend based on settings.

        Returns:
            An instance of a concrete Storage implementation (RedisStorage,
            SQLiteStorage, or MemoryStorage).

        """
        storage_type = self.settings.storage_type.lower()
        if storage_type == "redis":
            return RedisStorage(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
            )
        if storage_type == "sqlite":
            return SQLiteStorage(database=self.settings.sqlite_database)
        return MemoryStorage()

    def _create_api_clients(self, session: aiohttp.ClientSession) -> APIClients:
        """Create and return a collection of API clients.

        Args:
            session: The aiohttp client session to use for requests.

        Returns:
            An APIClients instance containing all initialized API clients.

        """
        client_config = ClientConfig(
            session=session,
            base_url=self.settings.base_url,
            retries=self.settings.api_retries,
            backoff_factor=self.settings.api_backoff_factor,
            timeout=self.settings.api_timeout,
            rate_limiter=self.rate_limiter,
            circuit_breaker=self.circuit_breaker,
            default_headers=self._default_api_headers(),
            header_provider=self._header_provider,
            endpoint_timeouts=self.settings.api_endpoint_timeouts,
            idempotency_header_name=self.settings.api_idempotency_header,
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

    def _default_api_headers(self) -> dict[str, str]:
        """Construct a dictionary of default headers for API requests.

        Includes authorization header if an API token is configured.

        Returns:
            A dictionary of HTTP headers.

        """
        headers = dict(self.settings.api_default_headers)
        token = (self.settings.api_auth_token or "").strip()
        if token:
            scheme = (self.settings.api_auth_scheme or "").strip()
            auth_value = f"{scheme} {token}".strip() if scheme else token
            headers.setdefault("Authorization", auth_value)
        return headers

    async def shutdown(self) -> None:
        """Shut down the application gracefully."""
        if self.websocket_client is not None:
            await self.websocket_client.close()
        if self.session is not None:
            await self.session.close()
        close_storage = getattr(self.storage, "close", None)
        if close_storage is not None:
            await close_storage()

    async def _handle_circuit_state_change(
        self, endpoint: str, state: CircuitBreakerState
    ) -> None:
        """Handle changes in the circuit breaker state for a given endpoint.

        If a circuit opens, the intake controller may be paused. If all
        circuits close, the intake controller may be resumed.

        Args:
            endpoint: The API endpoint whose circuit breaker state changed.
            state: The new state of the circuit breaker.

        """
        if self.intake_controller is None or self._circuit_state_lock is None:
            return

        pause = False
        resume = False
        pause_duration = float(
            max(
                self.settings.ingest_pause_seconds,
                self.settings.circuit_breaker_reset_timeout,
            )
        )
        async with self._circuit_state_lock:
            if state is CircuitBreakerState.OPEN:
                self._open_circuit_endpoints.add(endpoint)
                pause = True
            elif state is CircuitBreakerState.HALF_OPEN:
                self._open_circuit_endpoints.add(endpoint)
            elif state is CircuitBreakerState.CLOSED:
                self._open_circuit_endpoints.discard(endpoint)
                if not self._open_circuit_endpoints:
                    resume = True

        if pause:
            await self.intake_controller.pause(
                reason="circuit_open", duration=pause_duration
            )
        elif resume:
            await self.intake_controller.resume_now()

    async def _handle_rate_limit_wait(self, wait_time: float) -> None:
        """Handle a rate limit wait by pausing the intake controller.

        Args:
            wait_time: The duration (in seconds) to wait due to rate limiting.

        """
        if self.intake_controller is None:
            return

        pause_for = max(wait_time, self.settings.ingest_pause_seconds)
        await self.intake_controller.pause(reason="rate_limited", duration=pause_for)
