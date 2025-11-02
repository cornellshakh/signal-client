from __future__ import annotations

import pytest

from signal_client.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_service_in_memory():
    """Test that the in-memory storage works correctly."""
    # Arrange
    config = {"type": "in-memory"}
    storage_service = StorageService(config)

    # Act
    await storage_service.save("key1", "value1")
    result = await storage_service.read("key1")
    exists = await storage_service.exists("key1")
    await storage_service.delete("key1")
    exists_after_delete = await storage_service.exists("key1")

    # Assert
    assert result == "value1"
    assert exists is True
    assert exists_after_delete is False