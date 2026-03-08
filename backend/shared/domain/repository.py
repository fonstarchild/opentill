from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Generic repository interface for domain entities."""

    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        ...

    @abstractmethod
    def save(self, entity: T) -> T:
        ...

    @abstractmethod
    def delete(self, id: int) -> None:
        ...

    @abstractmethod
    def list(self) -> list[T]:
        ...
