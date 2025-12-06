from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def append(self, key: str, data: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def read_all(self, key: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_all(self, key: str) -> None:
        pass


class StorageError(Exception):
    pass
