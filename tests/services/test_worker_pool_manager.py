from __future__ import annotations

import asyncio
import json
import re
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from signal_client.bot import SignalClient
from signal_client.command import Command, command
from signal_client.context import Context
from signal_client.entities import ContextDependencies
from signal_client.metrics import MESSAGE_QUEUE_DEPTH, MESSAGE_QUEUE_LATENCY
from signal_client.services.message_parser import MessageParser
from signal_client.runtime.listener import MessageService
from signal_client.runtime.models import QueuedMessage
from signal_client.runtime.command_router import CommandRouter
from signal_client.runtime.worker_pool import Worker, WorkerConfig, WorkerPool


@pytest.fixture
def mock_context_factory():
    return MagicMock()


@pytest.fixture
def mock_queue():
    return MagicMock(spec=asyncio.Queue)


@pytest.fixture
def mock_message_parser():
    return MagicMock()


@pytest.fixture
def mock_command():
    command = AsyncMock()
    command.triggers = ["!test"]
    command.case_sensitive = False
    command.whitelisted = []
    return command


def _build_worker_pool(
    bot: SignalClient,
) -> tuple[WorkerPool, asyncio.Queue[QueuedMessage]]:
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    context_dependencies = bot.app.context_dependencies
    if context_dependencies is None:
        context_dependencies = ContextDependencies(
            accounts_client=bot.api_clients.accounts,
            attachments_client=bot.api_clients.attachments,
            contacts_client=bot.api_clients.contacts,
            devices_client=bot.api_clients.devices,
            general_client=bot.api_clients.general,
            groups_client=bot.api_clients.groups,
            identities_client=bot.api_clients.identities,
            messages_client=bot.api_clients.messages,
            profiles_client=bot.api_clients.profiles,
            reactions_client=bot.api_clients.reactions,
            receipts_client=bot.api_clients.receipts,
            search_client=bot.api_clients.search,
            sticker_packs_client=bot.api_clients.sticker_packs,
            lock_manager=bot.app.lock_manager,
            phone_number=bot.settings.phone_number,
        )
    context_factory = lambda message: Context(
        message=message, dependencies=context_dependencies
    )
    manager = WorkerPool(
        context_factory=context_factory,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )
    return manager, queue


@pytest.fixture
async def worker_pool_components(
    bot: SignalClient,
) -> tuple[WorkerPool, asyncio.Queue[QueuedMessage]]:
    await bot.app.initialize()
    return _build_worker_pool(bot)


@pytest.fixture
def make_raw_message():
    def _factory(
        message: str = "!test",
        *,
        source: str = "+1234567890",
        timestamp: int = 1234567890,
    ) -> str:
        return json.dumps(
            {
                "envelope": {
                    "source": source,
                    "timestamp": timestamp,
                    "dataMessage": {
                        "message": message,
                        "timestamp": timestamp,
                    },
                }
            }
        )

    return _factory


def test_command_router_respects_registration_order_and_case():
    router = CommandRouter()

    first = Command(triggers=["!Ping"], case_sensitive=True)
    second = Command(triggers=["!ping"])

    router.register(first)
    router.register(second)

    command, trigger = router.match("!Ping now")
    assert command is first
    assert trigger == "!Ping"

    command, trigger = router.match("!ping now")
    assert command is second
    assert trigger == "!ping"


@pytest.mark.asyncio
async def test_worker_process_matches_insensitive_trigger(
    mock_context_factory, mock_queue, mock_message_parser, mock_command
):
    # Arrange
    router = CommandRouter()
    router.register(mock_command)

    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        message_parser=mock_message_parser,
        router=router,
        middleware=[],
    )
    worker = Worker(worker_config)
    message = MagicMock()
    message.message = "!TeSt"
    mock_context_factory.return_value.message = message

    # Act
    await worker.process(message)

    # Assert
    mock_command.handle.assert_called_once()


@pytest.mark.asyncio
async def test_worker_process_matches_sensitive_trigger(
    mock_context_factory, mock_queue, mock_message_parser, mock_command
):
    # Arrange
    mock_command.case_sensitive = True
    router = CommandRouter()
    router.register(mock_command)

    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        message_parser=mock_message_parser,
        router=router,
        middleware=[],
    )
    worker = Worker(worker_config)
    message = MagicMock()
    message.message = "!test"
    mock_context_factory.return_value.message = message

    # Act
    await worker.process(message)

    # Assert
    mock_command.handle.assert_called_once()


@pytest.mark.asyncio
async def test_worker_process_matches_regex_trigger(
    mock_context_factory, mock_queue, mock_message_parser
):
    regex = re.compile(r"^/echo\s+(?P<text>.+)$", re.IGNORECASE)
    regex_command = Command(triggers=[regex])
    regex_handler = AsyncMock()
    regex_command.handle = regex_handler

    router = CommandRouter()
    router.register(regex_command)

    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        message_parser=mock_message_parser,
        router=router,
        middleware=[],
    )
    worker = Worker(worker_config)

    message = MagicMock()
    message.message = "/ECHO hello regex"
    mock_context_factory.return_value.message = message

    await worker.process(message)

    regex_handler.assert_called_once()


@pytest.mark.asyncio
@patch("signal_client.runtime.worker_pool.Worker")
async def test_worker_pool_starts_and_stops_workers(
    MockWorker, mock_context_factory, mock_queue, mock_message_parser, mock_command
):
    # Arrange
    pool_size = 2
    mock_worker_instance = MagicMock()
    mock_worker_instance.process_messages = AsyncMock()
    MockWorker.return_value = mock_worker_instance

    manager = WorkerPool(
        context_factory=mock_context_factory,
        queue=mock_queue,
        message_parser=mock_message_parser,
        pool_size=pool_size,
    )
    manager.register(mock_command)

    # Act
    manager.start()
    await manager._started.wait()
    manager.stop()
    await manager.join()

    # Assert
    assert MockWorker.call_count == pool_size
    assert mock_worker_instance.process_messages.call_count == pool_size
    assert mock_worker_instance.stop.call_count == pool_size
    for task in manager._tasks:
        assert task.done()


@pytest.mark.asyncio
async def test_worker_pool_end_to_end(
    mock_command: AsyncMock,
    worker_pool_components,
    make_raw_message,
) -> None:
    """
    End-to-end integration test for the WorkerPool.

    This test verifies that a message is processed from a real asyncio.Queue
    through the WorkerPool and a real Worker to a mocked command handler.
    """
    # Arrange
    manager, queue = worker_pool_components
    manager.register(mock_command)

    # Act
    manager.start()
    await queue.put(
        QueuedMessage(raw=make_raw_message("!test"), enqueued_at=time.perf_counter())
    )
    await queue.join()  # Wait for the message to be processed
    manager.stop()
    await manager.join()

    # Assert
    mock_command.handle.assert_called_once()


@pytest.mark.asyncio
async def test_worker_pool_handles_regex_triggers(
    worker_pool_components,
    make_raw_message,
) -> None:
    manager, queue = worker_pool_components

    regex = re.compile(r"^/echo\s+(?P<text>.+)$", re.IGNORECASE)
    regex_command = Command(triggers=[regex])
    regex_handler = AsyncMock()
    regex_command.handle = regex_handler

    manager.register(regex_command)

    manager.start()
    await queue.put(
        QueuedMessage(
            raw=make_raw_message("/ECHO hello"),
            enqueued_at=time.perf_counter(),
        )
    )
    await queue.join()
    manager.stop()
    await manager.join()

    regex_handler.assert_called_once()


@pytest.mark.asyncio
async def test_worker_middleware_execution(
    mock_command: AsyncMock,
    worker_pool_components,
    make_raw_message,
) -> None:
    manager, queue = worker_pool_components
    manager.register(mock_command)

    events: list[str] = []

    async def first(ctx, nxt):
        events.append("first")
        await nxt(ctx)

    async def second(ctx, nxt):
        events.append("second")
        await nxt(ctx)

    manager.register_middleware(first)
    manager.register_middleware(second)

    manager.start()
    await queue.put(
        QueuedMessage(
            raw=make_raw_message("!test", source="+1", timestamp=1),
            enqueued_at=time.perf_counter(),
        )
    )
    await queue.join()
    manager.stop()
    await manager.join()

    assert events == ["first", "second"]


@pytest.mark.asyncio
async def test_worker_updates_queue_metrics(
    worker_pool_components,
    make_raw_message,
) -> None:
    manager, queue = worker_pool_components

    observed = asyncio.Event()

    @command("!metrics")
    async def metrics_command(_context: Context) -> None:
        observed.set()

    manager.register(metrics_command)

    def histogram_count() -> float:
        samples = MESSAGE_QUEUE_LATENCY.collect()[0].samples
        for sample in samples:
            if sample.name.endswith("_count"):
                return sample.value
        return 0.0

    initial_count = histogram_count()

    manager.start()
    await queue.put(
        QueuedMessage(
            raw=make_raw_message("!metrics", source="+1", timestamp=1),
            enqueued_at=time.perf_counter() - 0.05,
        )
    )

    await asyncio.wait_for(observed.wait(), timeout=2)
    await queue.join()

    manager.stop()
    await manager.join()

    assert histogram_count() >= initial_count + 1

    depth_samples = MESSAGE_QUEUE_DEPTH.collect()[0].samples
    depth_value = next(
        sample.value for sample in depth_samples if sample.name == "message_queue_depth"
    )
    assert depth_value == 0


@pytest.mark.asyncio
async def test_message_service_and_worker_pipeline(
    worker_pool_components,
    make_raw_message,
) -> None:
    """Verify MessageService enqueues raw strings that workers consume."""

    manager, queue = worker_pool_components

    handled = asyncio.Event()

    @command("!ping")
    async def ping_command(_context: Context) -> None:
        handled.set()

    manager.register(ping_command)

    mock_websocket_client = AsyncMock()

    async def message_generator():
        yield make_raw_message("!ping")

    mock_websocket_client.listen = MagicMock(return_value=message_generator())
    message_service = MessageService(mock_websocket_client, queue, None)

    manager.start()
    listen_task = asyncio.create_task(message_service.listen())

    await asyncio.wait_for(handled.wait(), timeout=2)
    await queue.join()

    manager.stop()
    await manager.join()

    await listen_task
