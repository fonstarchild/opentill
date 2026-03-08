from __future__ import annotations
from typing import Generic, TypeVar, Optional, Type
from sqlmodel import Session, select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base SQLModel repository providing common CRUD operations."""

    def __init__(self, session: Session, model_class: Type[T]) -> None:
        self._session = session
        self._model_class = model_class

    def get(self, id: int) -> Optional[T]:
        return self._session.get(self._model_class, id)

    def save(self, entity: T) -> T:
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def delete(self, id: int) -> None:
        entity = self.get(id)
        if entity:
            self._session.delete(entity)
            self._session.commit()

    def list(self) -> list[T]:
        return list(self._session.exec(select(self._model_class)).all())
