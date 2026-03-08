from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class OrderItemInputDTO:
    product_id: int
    quantity: int


@dataclass
class PlaceOrderCommand:
    items: list[OrderItemInputDTO]
    payment_method: str
    discount_amount: float = 0.0
    amount_received: float = 0.0
    notes: str = ""
    customer_name: str = ""
    customer_email: str = ""
    currency: str = "EUR"


@dataclass
class ListOrdersQuery:
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = 1
    page_size: int = 50


@dataclass
class OrderItemDTO:
    id: int
    product_id: int
    product_name: str
    product_sku: str
    unit_price: float
    tax_rate: float
    quantity: int
    total_price: float


@dataclass
class OrderDTO:
    id: int
    reference: str
    created_at: datetime
    subtotal: float
    discount_amount: float
    total: float
    payment_method: str
    amount_received: float
    change_given: float
    notes: str
    customer_name: str
    customer_email: str
    status: str
    items: list[OrderItemDTO] = field(default_factory=list)
