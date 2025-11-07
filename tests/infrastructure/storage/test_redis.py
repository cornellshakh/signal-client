from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from signal_client.infrastructure.storage.redis import RedisStorage, StorageError


@pytest.fixture
def redis_storage(mocker: MockerFixture) -> RedisStorage:
    """Return a RedisStorage instance with a mocked redis client."""
    mock_redis_class = mocker.patch("redis.asyncio.Redis", autospec=True)
    mock_instance = mock_redis_class.return_value
    mock_instance.exists = AsyncMock()
    mock_instance.hgetall = AsyncMock()
    mock_instance.hset = AsyncMock()
    mock_instance.delete = AsyncMock()
    mock_instance.rpush = AsyncMock()
    mock_instance.lrange = AsyncMock()

    return RedisStorage(host="localhost", port=6379)


@pytest.mark.asyncio
async def test_exists(redis_storage: RedisStorage):
    """Test that exists returns True when key exists."""
    redis_storage.client.exists.return_value = 1
    assert await redis_storage.exists("test_key") is True
    redis_storage.client.exists.assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_exists_not_found(redis_storage: RedisStorage):
    """Test that exists returns False when key does not exist."""
    redis_storage.client.exists.return_value = 0
    assert await redis_storage.exists("test_key") is False
    redis_storage.client.exists.assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_read_hash(redis_storage: RedisStorage):
    """Test reading a hash from storage."""
    redis_storage.client.hgetall.return_value = {
        b"key1": b'"value1"',
        b"key2": b"123",
    }
    result = await redis_storage.read("test_key")
    assert result == {"key1": "value1", "key2": 123}
    redis_storage.client.hgetall.assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_read_hash_not_found(redis_storage: RedisStorage):
    """Test reading a non-existent hash raises StorageError."""
    redis_storage.client.hgetall.return_value = {}
    with pytest.raises(StorageError, match="Key 'test_key' not found"):
        await redis_storage.read("test_key")
    redis_storage.client.hgetall.assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_save_hash(redis_storage: RedisStorage):
    """Test saving a hash to storage."""
    data = {"key1": "value1", "key2": 123}
    await redis_storage.save("test_key", data)
    expected_mapping = {
        "key1": json.dumps("value1"),
        "key2": json.dumps(123),
    }
    redis_storage.client.hset.assert_awaited_once_with(
        "test_key", mapping=expected_mapping
    )


@pytest.mark.asyncio
async def test_save_empty_hash(redis_storage: RedisStorage):
    """Test that saving an empty hash deletes the key."""
    await redis_storage.save("test_key", {})
    redis_storage.client.delete.assert_awaited_once_with("test_key")
    redis_storage.client.hset.assert_not_called()


@pytest.mark.asyncio
async def test_delete(redis_storage: RedisStorage):
    """Test deleting a key from storage."""
    await redis_storage.delete("test_key")
    redis_storage.client.delete.assert_awaited_once_with("test_key")


@pytest.mark.asyncio
async def test_append_list(redis_storage: RedisStorage):
    """Test appending to a list in storage."""
    data = {"key1": "value1"}
    await redis_storage.append("test_key", data)
    redis_storage.client.rpush.assert_awaited_once_with("test_key", json.dumps(data))


@pytest.mark.asyncio
async def test_read_all_list(redis_storage: RedisStorage):
    """Test reading all items from a list."""
    redis_storage.client.lrange.return_value = [
        b'{"key1": "value1"}',
        b'{"key2": 123}',
    ]
    result = await redis_storage.read_all("test_key")
    assert result == [{"key1": "value1"}, {"key2": 123}]
    redis_storage.client.lrange.assert_awaited_once_with("test_key", 0, -1)


@pytest.mark.asyncio
async def test_read_all_empty_list(redis_storage: RedisStorage):
    """Test reading an empty list."""
    redis_storage.client.lrange.return_value = []
    result = await redis_storage.read_all("test_key")
    assert result == []
    redis_storage.client.lrange.assert_awaited_once_with("test_key", 0, -1)


@pytest.mark.asyncio
async def test_delete_all_list(redis_storage: RedisStorage):
    """Test deleting a list."""
    await redis_storage.delete_all("test_key")
    redis_storage.client.delete.assert_awaited_once_with("test_key")
