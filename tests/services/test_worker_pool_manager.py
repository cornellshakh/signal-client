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
from signal_client.metrics import MESSAGE_QUEUE_DEPTH, MESSAGE_QUEUE_LATENCY
from signal_client.services.message_parser import MessageParser
from signal_client.services.message_service import MessageService
from signal_client.services.models import QueuedMessage
from signal_client.services.worker_pool_manager import (
    Worker,
    WorkerConfig,
    WorkerPoolManager,
)


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


@pytest.mark.asyncio
async def test_worker_process_matches_insensitive_trigger(
    mock_context_factory, mock_queue, mock_message_parser, mock_command
):
    # Arrange
    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        commands={"!test": mock_command},
        message_parser=mock_message_parser,
        sensitive_trigger_regex=None,
        insensitive_trigger_regex=re.compile("(!test)", re.IGNORECASE),
        sensitive_triggers=[],
        insensitive_triggers=["!test"],
        regex_commands=[],
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
    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        commands={"!test": mock_command},
        message_parser=mock_message_parser,
        sensitive_trigger_regex=re.compile("(!test)"),
        insensitive_trigger_regex=None,
        sensitive_triggers=["!test"],
        insensitive_triggers=[],
        regex_commands=[],
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

    worker_config = WorkerConfig(
        context_factory=mock_context_factory,
        queue=mock_queue,
        commands={},
        message_parser=mock_message_parser,
        sensitive_trigger_regex=None,
        insensitive_trigger_regex=None,
        sensitive_triggers=[],
        insensitive_triggers=[],
        regex_commands=[(regex, regex_command)],
        middleware=[],
    )
    worker = Worker(worker_config)

    message = MagicMock()
    message.message = "/ECHO hello regex"
    mock_context_factory.return_value.message = message

    await worker.process(message)

    regex_handler.assert_called_once()


@pytest.mark.asyncio
@patch("signal_client.services.worker_pool_manager.Worker")
async def test_worker_pool_manager_starts_and_stops_workers(
    MockWorker, mock_context_factory, mock_queue, mock_message_parser, mock_command
):
    # Arrange
    pool_size = 2
    mock_worker_instance = MagicMock()
    mock_worker_instance.process_messages = AsyncMock()
    MockWorker.return_value = mock_worker_instance

    manager = WorkerPoolManager(
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
async def test_worker_pool_manager_end_to_end(
    bot: SignalClient, mock_command: AsyncMock
) -> None:
    """
    End-to-end integration test for the WorkerPoolManager.

    This test verifies that a message is processed from a real asyncio.Queue
    through the WorkerPoolManager and a real Worker to a mocked command handler.
    """
    # Arrange
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    manager = WorkerPoolManager(
        context_factory=bot.container.services_container.context,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )
    manager.register(mock_command)

    raw_message = {
        "envelope": {
            "source": "+1234567890",
            "timestamp": 1234567890,
            "dataMessage": {"message": "!test", "timestamp": 1234567890},
        }
    }
    raw_message_str = json.dumps(raw_message)

    # Act
    manager.start()
    await queue.put(QueuedMessage(raw=raw_message_str, enqueued_at=time.perf_counter()))
    await queue.join()  # Wait for the message to be processed
    manager.stop()
    await manager.join()

    # Assert
    mock_command.handle.assert_called_once()


@pytest.mark.asyncio
async def test_worker_pool_manager_handles_regex_triggers(bot: SignalClient) -> None:
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    manager = WorkerPoolManager(
        context_factory=bot.container.services_container.context,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )

    regex = re.compile(r"^/echo\s+(?P<text>.+)$", re.IGNORECASE)
    regex_command = Command(triggers=[regex])
    regex_handler = AsyncMock()
    regex_command.handle = regex_handler

    manager.register(regex_command)

    manager.start()
    await queue.put(
        QueuedMessage(
            raw=json.dumps(
                {
                    "envelope": {
                        "source": "+1234567890",
                        "timestamp": 1234567890,
                        "dataMessage": {
                            "message": "/ECHO hello",
                            "timestamp": 1234567890,
                        },
                    }
                }
            ),
            enqueued_at=time.perf_counter(),
        )
    )
    await queue.join()
    manager.stop()
    await manager.join()

    regex_handler.assert_called_once()


@pytest.mark.asyncio
async def test_worker_middleware_execution(
    bot: SignalClient, mock_command: AsyncMock
) -> None:
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    manager = WorkerPoolManager(
        context_factory=bot.container.services_container.context,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )
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

    raw_message = json.dumps(
        {
            "envelope": {
                "source": "+1",
                "timestamp": 1,
                "dataMessage": {"message": "!test", "timestamp": 1},
            }
        }
    )

    manager.start()
    await queue.put(QueuedMessage(raw=raw_message, enqueued_at=time.perf_counter()))
    await queue.join()
    manager.stop()
    await manager.join()

    assert events == ["first", "second"]


@pytest.mark.asyncio
async def test_worker_updates_queue_metrics(bot: SignalClient) -> None:
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    manager = WorkerPoolManager(
        context_factory=bot.container.services_container.context,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )

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
            raw=json.dumps(
                {
                    "envelope": {
                        "source": "+1",
                        "timestamp": 1,
                        "dataMessage": {"message": "!metrics", "timestamp": 1},
                    }
                }
            ),
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
async def test_message_service_and_worker_pipeline(bot: SignalClient) -> None:
    """Verify MessageService enqueues raw strings that workers consume."""

    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    message_parser = MessageParser()
    manager = WorkerPoolManager(
        context_factory=bot.container.services_container.context,
        queue=queue,
        message_parser=message_parser,
        pool_size=1,
    )

    handled = asyncio.Event()

    @command("!ping")
    async def ping_command(_context: Context) -> None:
        handled.set()

    manager.register(ping_command)

    mock_websocket_client = AsyncMock()

    async def message_generator():
        yield json.dumps(
            {
                "envelope": {
                    "source": "+1234567890",
                    "timestamp": 1234567890,
                    "dataMessage": {
                        "message": "!ping",
                        "timestamp": 1234567890,
                    },
                }
            }
        )

    mock_websocket_client.listen = MagicMock(return_value=message_generator())
    message_service = MessageService(mock_websocket_client, queue, None)

    manager.start()
    listen_task = asyncio.create_task(message_service.listen())
    await message_service._started.wait()

    await asyncio.wait_for(handled.wait(), timeout=2)
    await queue.join()

    manager.stop()
    await manager.join()

    await listen_task
