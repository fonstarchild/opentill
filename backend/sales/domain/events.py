from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from backend.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    reference: str = ""
    total: float = 0.0
    payment_method: str = ""


@dataclass(frozen=True)
class OrderVoided(DomainEvent):
    reference: str = ""
    order_id: Optional[int] = None
