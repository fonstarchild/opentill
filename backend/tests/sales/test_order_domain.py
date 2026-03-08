"""Tests for Sales domain — Order aggregate."""
import pytest
from decimal import Decimal
from backend.shared.domain.value_object import Money, OrderReference, TaxRate
from backend.sales.domain.order import Order
from backend.sales.domain.order_item import OrderItem
from backend.sales.domain.exceptions import (
    EmptyOrderError,
    OrderAlreadyVoidedError,
    OrderNotCompletedError,
)
from backend.sales.domain.events import OrderPlaced, OrderVoided


def make_item(quantity=2, price="9.99") -> OrderItem:
    return OrderItem(
        id=None,
        product_id=1,
        product_name="Test Product",
        product_sku="TEST-001",
        unit_price=Money(price, "EUR"),
        tax_rate=TaxRate(0.21),
        quantity=quantity,
    )


def make_order(items=None, discount="0.00", received="20.00") -> Order:
    if items is None:
        items = [make_item()]
    return Order.place(
        reference=OrderReference("OT-20240101-0001"),
        items=items,
        payment_method="CASH",
        discount_amount=Money(discount, "EUR"),
        amount_received=Money(received, "EUR"),
    )


class TestOrderPlacement:
    def test_place_records_event(self):
        order = make_order()
        events = order.collect_events()
        assert any(isinstance(e, OrderPlaced) for e in events)

    def test_empty_items_raises(self):
        with pytest.raises(EmptyOrderError):
            Order.place(
                reference=OrderReference("OT-20240101-0001"),
                items=[],
                payment_method="CASH",
                discount_amount=Money("0", "EUR"),
                amount_received=Money("0", "EUR"),
            )

    def test_initial_status_is_completed(self):
        order = make_order()
        assert order.status == "COMPLETED"


class TestOrderTotals:
    def test_subtotal_single_item(self):
        item = make_item(quantity=2, price="9.99")
        order = make_order(items=[item])
        assert order.subtotal.amount == pytest.approx(Decimal("19.98"))

    def test_subtotal_multiple_items(self):
        items = [make_item(quantity=1, price="10.00"), make_item(quantity=2, price="5.00")]
        order = make_order(items=items)
        assert order.subtotal.amount == pytest.approx(Decimal("20.00"))

    def test_total_with_discount(self):
        item = make_item(quantity=1, price="20.00")
        order = make_order(items=[item], discount="5.00", received="20.00")
        assert order.total.amount == pytest.approx(Decimal("15.00"))

    def test_total_discount_exceeding_subtotal(self):
        item = make_item(quantity=1, price="5.00")
        order = make_order(items=[item], discount="10.00", received="0.00")
        assert order.total.amount == Decimal("0")

    def test_change_given_for_cash(self):
        item = make_item(quantity=1, price="9.99")
        order = make_order(items=[item], received="20.00")
        assert order.change_given.amount == pytest.approx(Decimal("10.01"))

    def test_no_change_for_card(self):
        item = make_item(quantity=1, price="9.99")
        order = Order.place(
            reference=OrderReference("OT-20240101-0001"),
            items=[item],
            payment_method="TPV",
            discount_amount=Money("0", "EUR"),
            amount_received=Money("0", "EUR"),
        )
        assert order.change_given.amount == Decimal("0")


class TestOrderVoid:
    def test_void_completed_order(self):
        order = make_order()
        order.void()
        assert order.status == "VOID"

    def test_void_records_event(self):
        order = make_order()
        order.clear_events()
        order.void()
        events = order.collect_events()
        assert any(isinstance(e, OrderVoided) for e in events)

    def test_void_already_voided_raises(self):
        order = make_order()
        order.void()
        with pytest.raises(OrderAlreadyVoidedError):
            order.void()


class TestOrderItem:
    def test_subtotal_calculation(self):
        item = make_item(quantity=3, price="5.00")
        assert item.subtotal == Money("15.00", "EUR")

    def test_tax_amount(self):
        item = make_item(quantity=1, price="12.10")
        # tax_amount = price * rate / (1 + rate) = 12.10 * 0.21 / 1.21 ≈ 2.10
        assert item.tax_amount.amount == pytest.approx(Decimal("2.10"), abs=Decimal("0.01"))
