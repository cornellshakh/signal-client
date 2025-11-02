from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def read(self, key: str) -> dict[str, Any] | list[dict[str, Any]]:
        pass

    @abstractmethod
    async def save(self, key: str, data: dict[str, Any] | list[dict[str, Any]]) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class StorageError(Exception):
    pass
