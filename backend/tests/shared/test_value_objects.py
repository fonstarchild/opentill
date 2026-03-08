"""Tests for shared domain value objects."""
import pytest
from decimal import Decimal
from backend.shared.domain.value_object import Money, Barcode, SKU, OrderReference, Email, TaxRate


class TestMoney:
    def test_creates_with_amount_and_currency(self):
        m = Money(Decimal("9.99"), "EUR")
        assert m.amount == Decimal("9.99")
        assert m.currency == "EUR"

    def test_normalizes_currency_to_uppercase(self):
        m = Money(10, "eur")
        assert m.currency == "EUR"

    def test_accepts_float_string(self):
        m = Money("9.99", "EUR")
        assert m.amount == Decimal("9.99")

    def test_rejects_negative_amount(self):
        with pytest.raises(ValueError, match="negative"):
            Money(-1, "EUR")

    def test_add_same_currency(self):
        a = Money("5.00", "EUR")
        b = Money("3.00", "EUR")
        assert a + b == Money("8.00", "EUR")

    def test_add_different_currencies_raises(self):
        with pytest.raises(ValueError):
            Money("5.00", "EUR") + Money("5.00", "USD")

    def test_subtract(self):
        result = Money("10.00", "EUR") - Money("3.00", "EUR")
        assert result == Money("7.00", "EUR")

    def test_subtract_below_zero_raises(self):
        with pytest.raises(ValueError):
            Money("3.00", "EUR") - Money("10.00", "EUR")

    def test_multiply(self):
        m = Money("5.00", "EUR") * 3
        assert m.amount == Decimal("15.00")

    def test_equality(self):
        assert Money("9.99", "EUR") == Money("9.99", "EUR")
        assert Money("9.99", "EUR") != Money("9.99", "USD")

    def test_immutable(self):
        m = Money("9.99", "EUR")
        with pytest.raises(AttributeError):
            m._amount = Decimal("1.00")

    def test_as_float(self):
        assert Money("9.99", "EUR").as_float() == pytest.approx(9.99)


class TestBarcode:
    def test_creates_valid_barcode(self):
        b = Barcode("1234567890123")
        assert b.value == "1234567890123"

    def test_strips_whitespace(self):
        b = Barcode("  123  ")
        assert b.value == "123"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            Barcode("")

    def test_equality(self):
        assert Barcode("123") == Barcode("123")
        assert Barcode("123") != Barcode("456")

    def test_immutable(self):
        b = Barcode("123")
        with pytest.raises(AttributeError):
            b._value = "456"


class TestSKU:
    def test_creates_and_uppercases(self):
        s = SKU("test-001")
        assert s.value == "TEST-001"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            SKU("")

    def test_equality(self):
        assert SKU("abc") == SKU("ABC")


class TestOrderReference:
    def test_creates_reference(self):
        r = OrderReference("OT-20240101-0001")
        assert r.value == "OT-20240101-0001"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            OrderReference("")

    def test_equality(self):
        assert OrderReference("OT-20240101-0001") == OrderReference("OT-20240101-0001")


class TestEmail:
    def test_creates_valid_email(self):
        e = Email("Test@Example.com")
        assert e.value == "test@example.com"

    def test_rejects_invalid(self):
        with pytest.raises(ValueError):
            Email("notanemail")

    def test_rejects_no_tld(self):
        with pytest.raises(ValueError):
            Email("test@domain")


class TestTaxRate:
    def test_creates_valid_rate(self):
        t = TaxRate(0.21)
        assert t.as_float() == pytest.approx(0.21)

    def test_rejects_above_one(self):
        with pytest.raises(ValueError):
            TaxRate(1.5)

    def test_rejects_negative(self):
        with pytest.raises(ValueError):
            TaxRate(-0.1)

    def test_zero_is_valid(self):
        t = TaxRate(0)
        assert t.as_float() == 0.0

    def test_one_is_valid(self):
        t = TaxRate(1.0)
        assert t.as_float() == 1.0

    def test_as_percentage(self):
        t = TaxRate("0.21")
        assert t.as_percentage() == pytest.approx(Decimal("21"))

    def test_immutable(self):
        t = TaxRate(0.21)
        with pytest.raises(AttributeError):
            t._rate = Decimal("0.10")
