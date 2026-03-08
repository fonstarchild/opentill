from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from backend.shared.domain.aggregate import AggregateRoot
from backend.shared.domain.value_object import Money, OrderReference
from .order_item import OrderItem
from .events import OrderPlaced, OrderVoided
from .exceptions import OrderAlreadyVoidedError, EmptyOrderError, OrderNotCompletedError


class Order(AggregateRoot):
    """Order aggregate root."""

    STATUS_COMPLETED = "COMPLETED"
    STATUS_VOID = "VOID"
    STATUS_REFUNDED = "REFUNDED"

    def __init__(
        self,
        id: Optional[int],
        reference: OrderReference,
        items: list[OrderItem],
        payment_method: str,
        discount_amount: Money,
        amount_received: Money,
        created_at: Optional[datetime] = None,
        notes: str = "",
        customer_name: str = "",
        customer_email: str = "",
        status: str = STATUS_COMPLETED,
    ) -> None:
        super().__init__(id)
        self.reference = reference
        self.items = items
        self.payment_method = payment_method
        self.discount_amount = discount_amount
        self.amount_received = amount_received
        self.created_at = created_at or datetime.now(timezone.utc)
        self.notes = notes
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.status = status

    @classmethod
    def place(
        cls,
        reference: OrderReference,
        items: list[OrderItem],
        payment_method: str,
        discount_amount: Money,
        amount_received: Money,
        notes: str = "",
        customer_name: str = "",
        customer_email: str = "",
    ) -> "Order":
        if not items:
            raise EmptyOrderError("Order must have at least one item")

        order = cls(
            id=None,
            reference=reference,
            items=items,
            payment_method=payment_method,
            discount_amount=discount_amount,
            amount_received=amount_received,
            notes=notes,
            customer_name=customer_name,
            customer_email=customer_email,
            status=cls.STATUS_COMPLETED,
        )
        order._record_event(OrderPlaced(
            aggregate_id=None,
            reference=reference.value,
            total=order.total.as_float(),
            payment_method=payment_method,
        ))
        return order

    @property
    def subtotal(self) -> Money:
        if not self.items:
            currency = self.discount_amount.currency
            return Money(Decimal("0"), currency)
        total = self.items[0].subtotal
        for item in self.items[1:]:
            total = total + item.subtotal
        return total

    @property
    def total(self) -> Money:
        subtotal = self.subtotal
        try:
            result = subtotal - self.discount_amount
        except ValueError:
            result = Money(Decimal("0"), subtotal.currency)
        return result

    @property
    def change_given(self) -> Money:
        if self.payment_method != "CASH":
            return Money(Decimal("0"), self.amount_received.currency)
        try:
            return self.amount_received - self.total
        except ValueError:
            return Money(Decimal("0"), self.amount_received.currency)

    def void(self) -> None:
        if self.status == self.STATUS_VOID:
            raise OrderAlreadyVoidedError(f"Order {self.reference.value} is already voided")
        if self.status != self.STATUS_COMPLETED:
            raise OrderNotCompletedError(
                f"Cannot void order with status {self.status!r}"
            )
        self.status = self.STATUS_VOID
        self._record_event(OrderVoided(
            aggregate_id=self._id,
            reference=self.reference.value,
            order_id=self._id,
        ))
