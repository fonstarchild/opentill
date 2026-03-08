from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from backend.shared.domain.value_object import Money, OrderReference, TaxRate
from ..domain.order import Order
from ..domain.order_item import OrderItem
from ..domain.repository import IOrderRepository
from .sqlmodel_models import OrderTable, OrderItemTable


def _item_to_domain(row: OrderItemTable) -> OrderItem:
    return OrderItem(
        id=row.id,
        product_id=row.product_id,
        product_name=row.product_name,
        product_sku=row.product_sku,
        unit_price=Money(Decimal(str(row.unit_price)), row.currency),
        tax_rate=TaxRate(row.tax_rate),
        quantity=row.quantity,
    )


def _order_to_domain(row: OrderTable) -> Order:
    items = [_item_to_domain(i) for i in (row.items or [])]
    currency = row.currency
    return Order(
        id=row.id,
        reference=OrderReference(row.reference),
        items=items,
        payment_method=row.payment_method,
        discount_amount=Money(Decimal(str(row.discount_amount)), currency),
        amount_received=Money(Decimal(str(row.amount_received)), currency),
        created_at=row.created_at,
        notes=row.notes,
        customer_name=row.customer_name,
        customer_email=row.customer_email,
        status=row.status,
    )


class SqlModelOrderRepository(IOrderRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, id: int) -> Optional[Order]:
        row = self._session.get(OrderTable, id)
        return _order_to_domain(row) if row else None

    def get_by_reference(self, reference: str) -> Optional[Order]:
        row = self._session.exec(
            select(OrderTable).where(OrderTable.reference == reference)
        ).first()
        return _order_to_domain(row) if row else None

    def count_with_prefix(self, prefix: str) -> int:
        rows = self._session.exec(
            select(OrderTable).where(OrderTable.reference.startswith(prefix))
        ).all()
        return len(rows)

    def save(self, order: Order) -> Order:
        if order.id is not None:
            row = self._session.get(OrderTable, order.id)
        else:
            row = None

        if row is None:
            row = OrderTable()

        row.reference = order.reference.value
        row.payment_method = order.payment_method
        row.discount_amount = order.discount_amount.as_float()
        row.total = order.total.as_float()
        row.subtotal = order.subtotal.as_float()
        row.amount_received = order.amount_received.as_float()
        row.change_given = order.change_given.as_float()
        row.notes = order.notes
        row.customer_name = order.customer_name
        row.customer_email = order.customer_email
        row.status = order.status
        row.currency = order.discount_amount.currency
        if order.id:
            row.id = order.id

        self._session.add(row)
        self._session.flush()

        # Persist items only for new orders
        if order.id is None:
            for item in order.items:
                item_row = OrderItemTable(
                    order_id=row.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_sku=item.product_sku,
                    unit_price=item.unit_price.as_float(),
                    tax_rate=item.tax_rate.as_float(),
                    quantity=item.quantity,
                    total_price=item.subtotal.as_float(),
                    currency=item.unit_price.currency,
                )
                self._session.add(item_row)

        self._session.commit()
        self._session.refresh(row)
        return _order_to_domain(row)

    def delete(self, id: int) -> None:
        row = self._session.get(OrderTable, id)
        if row:
            self._session.delete(row)
            self._session.commit()

    def list(self) -> list[Order]:
        rows = self._session.exec(select(OrderTable)).all()
        return [_order_to_domain(r) for r in rows]

    def list_by_date_range(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Order]:
        q = select(OrderTable)
        if date_from:
            q = q.where(OrderTable.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            q = q.where(OrderTable.created_at <= datetime.combine(date_to, datetime.max.time()))
        q = q.order_by(OrderTable.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return [_order_to_domain(r) for r in self._session.exec(q).all()]
