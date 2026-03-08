from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExternalProduct:
    external_id: str
    name: str
    sku: str
    price: float
    stock: int
    barcode: str = ""
    category: str = ""
    description: str = ""
    tax_rate: float = 0.0
    currency: str = "EUR"
    active: bool = True
    raw: dict = field(default_factory=dict)


@dataclass
class ExternalOrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    tax_rate: float = 0.0


@dataclass
class ExternalOrder:
    external_id: str
    reference: str
    status: str
    total: float
    currency: str
    items: list[ExternalOrderItem] = field(default_factory=list)
    customer_name: str = ""
    customer_email: str = ""
    created_at: Optional[datetime] = None
    raw: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    success: bool
    external_id: str = ""
    message: str = ""
    errors: list[str] = field(default_factory=list)
