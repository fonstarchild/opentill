from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int
    product_name: str        # snapshot
    product_sku: str         # snapshot
    unit_price: float        # snapshot
    tax_rate: float          # snapshot
    quantity: int
    total_price: float       # unit_price * quantity

    order: Optional["Order"] = Relationship(back_populates="items")


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reference: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subtotal: float
    discount_amount: float = Field(default=0.0)
    total: float
    payment_method: str       # CASH | TPV | BIZUM | TRANSFER | STRIPE | SUMUP | ...
    amount_received: float = Field(default=0.0)   # for cash change calculation
    change_given: float = Field(default=0.0)
    notes: str = Field(default="")
    customer_name: str = Field(default="")
    customer_email: str = Field(default="")
    status: str = Field(default="COMPLETED")  # COMPLETED | REFUNDED | VOID

    items: List[OrderItem] = Relationship(back_populates="order")


# ── Input schemas ──────────────────────────────────────────────────────────────

class OrderItemInput(SQLModel):
    product_id: int
    quantity: int


class OrderCreate(SQLModel):
    items: List[OrderItemInput]
    payment_method: str
    discount_amount: float = 0.0
    amount_received: float = 0.0
    notes: str = ""
    customer_name: str = ""
    customer_email: str = ""


# ── Output schema (with items inline) ─────────────────────────────────────────

class OrderItemOut(SQLModel):
    id: int
    product_id: int
    product_name: str
    product_sku: str
    unit_price: float
    tax_rate: float
    quantity: int
    total_price: float


class OrderOut(SQLModel):
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
    items: List[OrderItemOut]
