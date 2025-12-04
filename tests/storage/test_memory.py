import pytest

from signal_client.storage.memory import MemoryStorage


@pytest.fixture
def memory_storage():
    return MemoryStorage()


async def test_memory_storage_append_and_read(memory_storage: MemoryStorage):
    await memory_storage.append("test_key", {"data": "test_value"})
    result = await memory_storage.read_all("test_key")
    assert result == [{"data": "test_value"}]


async def test_memory_storage_read_all_empty(memory_storage: MemoryStorage):
    result = await memory_storage.read_all("non_existent_key")
    assert result == []


async def test_memory_storage_delete_all(memory_storage: MemoryStorage):
    await memory_storage.append("test_key", {"data": "test_value"})
    await memory_storage.delete_all("test_key")
    result = await memory_storage.read_all("test_key")
    assert result == []


async def test_memory_storage_close(memory_storage: MemoryStorage):
    await memory_storage.append("test_key", {"data": "test_value"})
    await memory_storage.close()
    result = await memory_storage.read_all("test_key")
    assert result == []
