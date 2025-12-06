"""Tests for the message service."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from signal_client.runtime.listener import BackpressurePolicy, MessageService
from signal_client.runtime.models import QueuedMessage


@pytest.fixture
def mock_websocket_client():
    """Return a mock websocket client."""
    mock = AsyncMock()
    mock.listen = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_listen_puts_messages_on_queue(mock_websocket_client):
    """Test that listen puts messages on the queue."""
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

    await asyncio.wait_for(service.listen(), timeout=1)

    assert queue.qsize() == len(messages)
    received = [await queue.get() for _ in range(len(messages))]
    assert [item.raw for item in received] == messages


@pytest.mark.asyncio
async def test_listen_drops_oldest_when_queue_full(mock_websocket_client):
    """Test that listen drops the oldest message when the queue is full."""
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
        backpressure_policy=BackpressurePolicy.DROP_OLDEST,
    )

    await asyncio.wait_for(service.listen(), timeout=1)

    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[-1]
    dead_letter_queue.send.assert_not_called()


@pytest.mark.asyncio
async def test_listen_sends_to_dlq_when_drop_disabled(mock_websocket_client):
    """Test that listen sends to the DLQ when drop is disabled."""
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
        backpressure_policy=BackpressurePolicy.FAIL_FAST,
    )

    await asyncio.wait_for(service.listen(), timeout=1)

    dead_letter_queue.send.assert_called_once_with(json.loads(messages[-1]))
    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[0]


@pytest.mark.asyncio
async def test_listen_sends_raw_payload_to_dlq_when_json_invalid(mock_websocket_client):
    """Test that listen sends raw payload to DLQ when JSON is invalid."""
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
        backpressure_policy=BackpressurePolicy.FAIL_FAST,
    )

    await asyncio.wait_for(service.listen(), timeout=1)

    dead_letter_queue.send.assert_called_once_with({"raw": "not-json"})
    assert queue.qsize() == 1
    queued = await queue.get()
    assert queued.raw == messages[0]


@pytest.mark.asyncio
async def test_integration_websocket_to_queue():
    """Test integration of websocket to queue."""
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
    await asyncio.wait_for(listen_task, timeout=1)

    # Assert
    assert real_queue.qsize() == len(messages)
    for msg in messages:
        queued = await real_queue.get()
        assert queued.raw == msg
