from __future__ import annotations
from typing import Any
from .entity import BaseEntity
from .domain_event import DomainEvent


class AggregateRoot(BaseEntity):
    """Base class for aggregate roots. Manages domain events."""

    def __init__(self, id: Any) -> None:
        super().__init__(id)
        self._events: list[DomainEvent] = []

    def _record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()
