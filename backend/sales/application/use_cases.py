from __future__ import annotations
from decimal import Decimal
from typing import Optional
from datetime import date

from backend.shared.domain.exceptions import NotFoundError
from backend.shared.domain.value_object import Money, OrderReference, TaxRate
from ..domain.order import Order
from ..domain.order_item import OrderItem
from ..domain.repository import IOrderRepository
from ..domain.services import DateSequenceReferenceGenerator
from ..domain.exceptions import EmptyOrderError
from .dtos import (
    PlaceOrderCommand,
    ListOrdersQuery,
    OrderDTO,
    OrderItemDTO,
)

# Import catalog repo to resolve product details
from backend.catalog.domain.repository import IProductRepository


def _item_to_dto(item: OrderItem) -> OrderItemDTO:
    return OrderItemDTO(
        id=item.id or 0,
        product_id=item.product_id,
        product_name=item.product_name,
        product_sku=item.product_sku,
        unit_price=item.unit_price.as_float(),
        tax_rate=item.tax_rate.as_float(),
        quantity=item.quantity,
        total_price=item.subtotal.as_float(),
    )


def _order_to_dto(order: Order) -> OrderDTO:
    return OrderDTO(
        id=order.id or 0,
        reference=order.reference.value,
        created_at=order.created_at,
        subtotal=order.subtotal.as_float(),
        discount_amount=order.discount_amount.as_float(),
        total=order.total.as_float(),
        payment_method=order.payment_method,
        amount_received=order.amount_received.as_float(),
        change_given=order.change_given.as_float(),
        notes=order.notes,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        status=order.status,
        items=[_item_to_dto(i) for i in order.items],
    )


class PlaceOrder:
    def __init__(
        self,
        order_repo: IOrderRepository,
        product_repo: IProductRepository,
    ) -> None:
        self._order_repo = order_repo
        self._product_repo = product_repo

    def execute(self, cmd: PlaceOrderCommand) -> OrderDTO:
        if not cmd.items:
            raise EmptyOrderError("Order must have at least one item")

        currency = cmd.currency
        order_items: list[OrderItem] = []

        for item_input in cmd.items:
            product = self._product_repo.get(item_input.product_id)
            if not product:
                raise NotFoundError(f"Product {item_input.product_id} not found")
            product.adjust_stock(-item_input.quantity)
            self._product_repo.save(product)

            order_items.append(OrderItem(
                id=None,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku.value,
                unit_price=Money(product.price.amount, currency),
                tax_rate=product.tax_rate,
                quantity=item_input.quantity,
            ))

        ref_gen = DateSequenceReferenceGenerator(
            count_today_fn=self._order_repo.count_with_prefix
        )
        reference = OrderReference(ref_gen.next_reference())
        discount = Money(Decimal(str(cmd.discount_amount)), currency)
        received = Money(Decimal(str(cmd.amount_received)), currency)

        order = Order.place(
            reference=reference,
            items=order_items,
            payment_method=cmd.payment_method,
            discount_amount=discount,
            amount_received=received,
            notes=cmd.notes,
            customer_name=cmd.customer_name,
            customer_email=cmd.customer_email,
        )
        saved = self._order_repo.save(order)
        return _order_to_dto(saved)


class VoidOrder:
    def __init__(self, order_repo: IOrderRepository, product_repo: IProductRepository) -> None:
        self._order_repo = order_repo
        self._product_repo = product_repo

    def execute(self, order_id: int) -> OrderDTO:
        order = self._order_repo.get(order_id)
        if not order:
            raise NotFoundError(f"Order not found: {order_id}")
        order.void()
        # Restore stock
        for item in order.items:
            product = self._product_repo.get(item.product_id)
            if product:
                product.adjust_stock(item.quantity, reason="order voided")
                self._product_repo.save(product)
        saved = self._order_repo.save(order)
        return _order_to_dto(saved)


class GetOrder:
    def __init__(self, repo: IOrderRepository) -> None:
        self._repo = repo

    def execute(self, order_id: int) -> OrderDTO:
        order = self._repo.get(order_id)
        if not order:
            raise NotFoundError(f"Order not found: {order_id}")
        return _order_to_dto(order)


class ListOrders:
    def __init__(self, repo: IOrderRepository) -> None:
        self._repo = repo

    def execute(self, query: ListOrdersQuery) -> list[OrderDTO]:
        orders = self._repo.list_by_date_range(
            date_from=query.date_from,
            date_to=query.date_to,
            page=query.page,
            page_size=query.page_size,
        )
        return [_order_to_dto(o) for o in orders]
