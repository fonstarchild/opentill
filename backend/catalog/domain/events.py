from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from backend.shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class ProductCreated(DomainEvent):
    sku: str = ""
    name: str = ""


@dataclass(frozen=True)
class StockAdjusted(DomainEvent):
    product_id: Optional[int] = None
    delta: int = 0
    new_stock: int = 0
    reason: str = ""


@dataclass(frozen=True)
class ProductDeactivated(DomainEvent):
    product_id: Optional[int] = None
