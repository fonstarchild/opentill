from __future__ import annotations
from decimal import Decimal
from typing import Optional

from backend.shared.domain.aggregate import AggregateRoot
from backend.shared.domain.value_object import Money, Barcode, SKU, TaxRate
from .events import ProductCreated, StockAdjusted, ProductDeactivated
from .exceptions import InsufficientStockError


class Product(AggregateRoot):
    """Product aggregate root."""

    def __init__(
        self,
        id: Optional[int],
        sku: SKU,
        name: str,
        price: Money,
        tax_rate: TaxRate,
        stock: int = 0,
        barcode: Optional[Barcode] = None,
        cost: Money = None,
        category: str = "",
        description: str = "",
        active: bool = True,
    ) -> None:
        super().__init__(id)
        self.sku = sku
        self.name = name
        self.price = price
        self.tax_rate = tax_rate
        self.stock = stock
        self.barcode = barcode
        self.cost = cost or Money(Decimal("0"), price.currency)
        self.category = category
        self.description = description
        self.active = active

    @classmethod
    def create(
        cls,
        sku: SKU,
        name: str,
        price: Money,
        tax_rate: TaxRate,
        stock: int = 0,
        barcode: Optional[Barcode] = None,
        cost: Optional[Money] = None,
        category: str = "",
        description: str = "",
    ) -> "Product":
        product = cls(
            id=None,
            sku=sku,
            name=name,
            price=price,
            tax_rate=tax_rate,
            stock=stock,
            barcode=barcode,
            cost=cost,
            category=category,
            description=description,
        )
        product._record_event(ProductCreated(
            aggregate_id=None,
            sku=sku.value,
            name=name,
        ))
        return product

    def adjust_stock(self, delta: int, reason: str = "") -> None:
        new_stock = self.stock + delta
        if new_stock < 0:
            raise InsufficientStockError(
                f"Insufficient stock for product '{self.name}': "
                f"available {self.stock}, requested {-delta}"
            )
        self.stock = new_stock
        self._record_event(StockAdjusted(
            aggregate_id=self._id,
            product_id=self._id,
            delta=delta,
            new_stock=new_stock,
            reason=reason,
        ))

    def deactivate(self) -> None:
        self.active = False
        self._record_event(ProductDeactivated(aggregate_id=self._id, product_id=self._id))

    def update(
        self,
        name: Optional[str] = None,
        price: Optional[Money] = None,
        cost: Optional[Money] = None,
        tax_rate: Optional[TaxRate] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> None:
        if name is not None:
            self.name = name
        if price is not None:
            self.price = price
        if cost is not None:
            self.cost = cost
        if tax_rate is not None:
            self.tax_rate = tax_rate
        if category is not None:
            self.category = category
        if description is not None:
            self.description = description
        if active is not None:
            self.active = active
