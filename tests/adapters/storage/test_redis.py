"""Tests for the RedisStorage client."""

from __future__ import annotations

import json
from typing import cast
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from signal_client.adapters.storage.redis import RedisStorage


@pytest.fixture
def redis_storage(mocker: MockerFixture) -> RedisStorage:
    """Return a RedisStorage instance with a mocked redis client."""
    mock_redis_class = mocker.patch("redis.asyncio.Redis", autospec=True)
    mock_instance = mock_redis_class.return_value
    mock_instance.rpush = AsyncMock()
    mock_instance.lrange = AsyncMock()
    mock_instance.delete = AsyncMock()
    mock_instance.close = AsyncMock()

    return RedisStorage(host="localhost", port=6379)


@pytest.mark.asyncio
async def test_append_list(redis_storage: RedisStorage):
    """Test appending to a list in storage."""
    data = {"key1": "value1"}
    await redis_storage.append("test_key", data)
    cast("AsyncMock", redis_storage.client.rpush).assert_awaited_once_with(
        "test_key",
        json.dumps(data),
    )


@pytest.mark.asyncio
async def test_read_all_list(redis_storage: RedisStorage):
    """Test reading all items from a list."""
    cast("AsyncMock", redis_storage.client.lrange).return_value = [
        b'{"key1": "value1"}',
        b'{"key2": 123}',
    ]
    result = await redis_storage.read_all("test_key")  # noqa: F841
    cast("AsyncMock", redis_storage.client.lrange).assert_awaited_once_with(
        "test_key",
        0,
        -1,
    )


@pytest.mark.asyncio
async def test_read_all_empty_list(redis_storage: RedisStorage):
    """Test reading an empty list."""
    cast("AsyncMock", redis_storage.client.lrange).return_value = []
    result = await redis_storage.read_all("test_key")
    assert result == []
    cast("AsyncMock", redis_storage.client.lrange).assert_awaited_once_with(
        "test_key",
        0,
        -1,
    )


@pytest.mark.asyncio
async def test_delete_all_list(redis_storage: RedisStorage):
    """Test deleting a list."""
    await redis_storage.delete_all("test_key")
    cast("AsyncMock", redis_storage.client.delete).assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_close(redis_storage: RedisStorage):
    """Test closing the redis client."""
    await redis_storage.close()
    cast("AsyncMock", redis_storage.client.close).assert_awaited_once_with()
