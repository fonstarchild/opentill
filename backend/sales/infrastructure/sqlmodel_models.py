from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship


class OrderItemTable(SQLModel, table=True):
    __tablename__ = "orderitem"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="ordertable.id")
    product_id: int
    product_name: str
    product_sku: str
    unit_price: float
    tax_rate: float
    quantity: int
    total_price: float
    currency: str = Field(default="EUR")

    order: Optional["OrderTable"] = Relationship(back_populates="items")


class OrderTable(SQLModel, table=True):
    __tablename__ = "ordertable"

    id: Optional[int] = Field(default=None, primary_key=True)
    reference: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subtotal: float
    discount_amount: float = Field(default=0.0)
    total: float
    payment_method: str
    amount_received: float = Field(default=0.0)
    change_given: float = Field(default=0.0)
    notes: str = Field(default="")
    customer_name: str = Field(default="")
    customer_email: str = Field(default="")
    status: str = Field(default="COMPLETED")
    currency: str = Field(default="EUR")

    items: List[OrderItemTable] = Relationship(back_populates="order")
