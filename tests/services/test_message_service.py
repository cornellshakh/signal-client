from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from signal_client.services.message_service import MessageService
from signal_client.services.models import QueuedMessage


@pytest.fixture
def mock_websocket_client():
    mock = AsyncMock()
    mock.listen = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_listen_puts_messages_on_queue(mock_websocket_client):
    messages = ['{"foo": "bar"}', '{"baz": "qux"}']

    async def message_generator():
        for msg in messages:
            yield msg

    mock_websocket_client.listen.return_value = message_generator()
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue(maxsize=10)
    service = MessageService(
        mock_websocket_client,
        queue,
        dead_letter_queue=None,
        enqueue_timeout=0.1,
    )

    listen_task = asyncio.create_task(service.listen())
    await service._started.wait()
    await asyncio.wait_for(listen_task, timeout=1)

    assert queue.qsize() == len(messages)
    received = [await queue.get() for _ in range(len(messages))]
    assert [item.raw for item in received] == messages


@pytest.mark.asyncio
async def test_listen_drops_oldest_when_queue_full(mock_websocket_client):
    messages = [json.dumps({"idx": 1}), json.dumps({"idx": 2})]

    async def async_generator():
        for msg in messages:
            yield msg

    mock_websocket_client.listen.return_value = async_generator()
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue(maxsize=1)
    dead_letter_queue = AsyncMock()
    service = MessageService(
        mock_websocket_client,
        queue,
        dead_letter_queue,
        enqueue_timeout=0.01,
        drop_oldest_on_timeout=True,
    )

    listen_task = asyncio.create_task(service.listen())
    await service._started.wait()
    await asyncio.wait_for(listen_task, timeout=1)

    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[-1]
    dead_letter_queue.send.assert_not_called()


@pytest.mark.asyncio
async def test_listen_sends_to_dlq_when_drop_disabled(mock_websocket_client):
    messages = [json.dumps({"idx": 1}), json.dumps({"idx": 2})]

    async def async_generator():
        for msg in messages:
            yield msg

    mock_websocket_client.listen.return_value = async_generator()
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue(maxsize=1)
    dead_letter_queue = AsyncMock()
    service = MessageService(
        mock_websocket_client,
        queue,
        dead_letter_queue,
        enqueue_timeout=0.01,
        drop_oldest_on_timeout=False,
    )

    listen_task = asyncio.create_task(service.listen())
    await service._started.wait()
    await asyncio.wait_for(listen_task, timeout=1)

    dead_letter_queue.send.assert_called_once_with(json.loads(messages[-1]))
    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[0]


@pytest.mark.asyncio
async def test_listen_sends_raw_payload_to_dlq_when_json_invalid(mock_websocket_client):
    messages = [json.dumps({"idx": 1}), "not-json"]

    async def async_generator():
        for msg in messages:
            yield msg

    mock_websocket_client.listen.return_value = async_generator()
    queue: asyncio.Queue[QueuedMessage] = asyncio.Queue(maxsize=1)
    dead_letter_queue = AsyncMock()
    service = MessageService(
        mock_websocket_client,
        queue,
        dead_letter_queue,
        enqueue_timeout=0.01,
        drop_oldest_on_timeout=False,
    )

    listen_task = asyncio.create_task(service.listen())
    await service._started.wait()
    await asyncio.wait_for(listen_task, timeout=1)

    dead_letter_queue.send.assert_called_once_with({"raw": "not-json"})
    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[0]


@pytest.mark.asyncio
async def test_integration_websocket_to_queue():
    # Arrange
    mock_websocket_client = AsyncMock()
    mock_websocket_client.listen = MagicMock()
    messages = ['{"key": "value1"}', '{"key": "value2"}']

    async def message_generator():
        for msg in messages:
            yield msg

    mock_websocket_client.listen.return_value = message_generator()
    real_queue: asyncio.Queue[QueuedMessage] = asyncio.Queue()
    service = MessageService(mock_websocket_client, real_queue, None)

    # Act
    listen_task = asyncio.create_task(service.listen())
    await service._started.wait()
    listen_task.cancel()
    try:
        await listen_task
    except asyncio.CancelledError:
        pass

    # Assert
    assert real_queue.qsize() == len(messages)
    for msg in messages:
        queued = await real_queue.get()
        assert queued.raw == msg
