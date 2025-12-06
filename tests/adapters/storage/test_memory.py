"""Tests for the in-memory storage."""

import pytest

from signal_client.adapters.storage.memory import MemoryStorage


@pytest.fixture
def memory_storage():
    """Return an in-memory storage instance."""
    return MemoryStorage()


async def test_memory_storage_append_and_read(memory_storage: MemoryStorage):
    """Test appending and reading from memory storage."""
    await memory_storage.append("test_key", {"data": "test_value"})
    result = await memory_storage.read_all("test_key")
    assert result == [{"data": "test_value"}]


async def test_memory_storage_read_all_empty(memory_storage: MemoryStorage):
    """Test reading from an empty key in memory storage."""
    result = await memory_storage.read_all("non_existent_key")
    assert result == []


async def test_memory_storage_delete_all(memory_storage: MemoryStorage):
    """Test deleting all items for a key in memory storage."""
    await memory_storage.append("test_key", {"data": "test_value"})
    await memory_storage.delete_all("test_key")
    result = await memory_storage.read_all("test_key")
    assert result == []


async def test_memory_storage_close(memory_storage: MemoryStorage):
    """Test closing memory storage."""
    await memory_storage.append("test_key", {"data": "test_value"})
    await memory_storage.close()
    result = await memory_storage.read_all("test_key")
    assert result == []
