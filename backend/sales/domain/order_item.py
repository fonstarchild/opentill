from __future__ import annotations
from decimal import Decimal
from typing import Optional

from backend.shared.domain.entity import BaseEntity
from backend.shared.domain.value_object import Money, TaxRate


class OrderItem(BaseEntity):
    """A line item within an order (product snapshot + quantity)."""

    def __init__(
        self,
        id: Optional[int],
        product_id: int,
        product_name: str,
        product_sku: str,
        unit_price: Money,
        tax_rate: TaxRate,
        quantity: int,
    ) -> None:
        super().__init__(id)
        self.product_id = product_id
        self.product_name = product_name
        self.product_sku = product_sku
        self.unit_price = unit_price
        self.tax_rate = tax_rate
        self.quantity = quantity

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity

    @property
    def tax_amount(self) -> Money:
        """Tax amount included in the price (assuming price includes tax)."""
        factor = self.tax_rate.rate / (Decimal("1") + self.tax_rate.rate)
        return Money(self.subtotal.amount * factor, self.unit_price.currency)
