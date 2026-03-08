from __future__ import annotations
from typing import Any


class BaseEntity:
    """Base class for all domain entities. Identity-based equality."""

    def __init__(self, id: Any) -> None:
        self._id = id

    @property
    def id(self) -> Any:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash((self.__class__, self._id))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"
