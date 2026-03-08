"""Tests for Catalog domain — Product aggregate."""
import pytest
from decimal import Decimal
from backend.shared.domain.value_object import Money, Barcode, SKU, TaxRate
from backend.catalog.domain.product import Product
from backend.catalog.domain.exceptions import InsufficientStockError
from backend.catalog.domain.events import ProductCreated, StockAdjusted, ProductDeactivated


def make_product(stock=10) -> Product:
    return Product.create(
        sku=SKU("TEST-001"),
        name="Test Product",
        price=Money("9.99", "EUR"),
        tax_rate=TaxRate(0.21),
        stock=stock,
        barcode=Barcode("1234567890123"),
        cost=Money("5.00", "EUR"),
        category="General",
    )


class TestProductCreate:
    def test_create_records_event(self):
        p = make_product()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ProductCreated)
        assert events[0].sku == "TEST-001"

    def test_initial_state(self):
        p = make_product(stock=5)
        assert p.stock == 5
        assert p.active is True
        assert p.name == "Test Product"
        assert p.price == Money("9.99", "EUR")

    def test_id_is_none_before_save(self):
        p = make_product()
        assert p.id is None


class TestProductStockAdjustment:
    def test_add_stock(self):
        p = make_product(stock=10)
        p.adjust_stock(5)
        assert p.stock == 15

    def test_remove_stock(self):
        p = make_product(stock=10)
        p.adjust_stock(-3)
        assert p.stock == 7

    def test_remove_all_stock(self):
        p = make_product(stock=10)
        p.adjust_stock(-10)
        assert p.stock == 0

    def test_insufficient_stock_raises(self):
        p = make_product(stock=5)
        with pytest.raises(InsufficientStockError):
            p.adjust_stock(-6)

    def test_stock_adjustment_records_event(self):
        p = make_product(stock=10)
        p.clear_events()
        p.adjust_stock(3, reason="restock")
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], StockAdjusted)
        assert events[0].delta == 3
        assert events[0].new_stock == 13
        assert events[0].reason == "restock"


class TestProductDeactivation:
    def test_deactivate_sets_inactive(self):
        p = make_product()
        p.deactivate()
        assert p.active is False

    def test_deactivate_records_event(self):
        p = make_product()
        p.clear_events()
        p.deactivate()
        events = p.collect_events()
        assert any(isinstance(e, ProductDeactivated) for e in events)


class TestProductUpdate:
    def test_update_name(self):
        p = make_product()
        p.update(name="New Name")
        assert p.name == "New Name"

    def test_update_price(self):
        p = make_product()
        p.update(price=Money("19.99", "EUR"))
        assert p.price == Money("19.99", "EUR")

    def test_partial_update_leaves_rest_unchanged(self):
        p = make_product()
        original_stock = p.stock
        p.update(name="Changed")
        assert p.stock == original_stock
