from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class ValueObject:
    """Base class for value objects. Equality by value, immutable."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash((self.__class__, tuple(sorted(self.__dict__.items()))))


# ── Common Value Objects ──────────────────────────────────────────────────────

class Money(ValueObject):
    """Monetary amount with currency."""

    def __init__(self, amount: Decimal | float | str, currency: str = "EUR") -> None:
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount < 0:
            raise ValueError(f"Money amount cannot be negative: {amount}")
        object.__setattr__(self, "_amount", amount)
        object.__setattr__(self, "_currency", currency.upper())

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Money is immutable")

    def __add__(self, other: "Money") -> "Money":
        if self._currency != other._currency:
            raise ValueError(f"Cannot add {self._currency} and {other._currency}")
        return Money(self._amount + other._amount, self._currency)

    def __sub__(self, other: "Money") -> "Money":
        if self._currency != other._currency:
            raise ValueError(f"Cannot subtract {self._currency} and {other._currency}")
        result = self._amount - other._amount
        if result < 0:
            raise ValueError("Subtraction would result in negative Money")
        return Money(result, self._currency)

    def __mul__(self, factor: int | float | Decimal) -> "Money":
        return Money(self._amount * Decimal(str(factor)), self._currency)

    def __repr__(self) -> str:
        return f"Money({self._amount}, {self._currency!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount == other._amount and self._currency == other._currency

    def __hash__(self) -> int:
        return hash((self.__class__, self._amount, self._currency))

    def as_float(self) -> float:
        return float(self._amount)


class Barcode(ValueObject):
    """Product barcode (EAN-13, UPC-A, etc.)."""

    def __init__(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Barcode cannot be empty")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Barcode is immutable")

    def __repr__(self) -> str:
        return f"Barcode({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Barcode):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash((self.__class__, self._value))


class SKU(ValueObject):
    """Stock Keeping Unit identifier."""

    def __init__(self, value: str) -> None:
        value = value.strip().upper()
        if not value:
            raise ValueError("SKU cannot be empty")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("SKU is immutable")

    def __repr__(self) -> str:
        return f"SKU({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SKU):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash((self.__class__, self._value))


class OrderReference(ValueObject):
    """Order reference in format OT-YYYYMMDD-XXXX."""

    def __init__(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("OrderReference cannot be empty")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("OrderReference is immutable")

    def __repr__(self) -> str:
        return f"OrderReference({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OrderReference):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash((self.__class__, self._value))


class Email(ValueObject):
    """Email address value object."""

    def __init__(self, value: str) -> None:
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"Invalid email address: {value!r}")
        object.__setattr__(self, "_value", value)

    @property
    def value(self) -> str:
        return self._value

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("Email is immutable")

    def __repr__(self) -> str:
        return f"Email({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash((self.__class__, self._value))


class TaxRate(ValueObject):
    """Tax rate as a fraction (0.21 = 21%)."""

    def __init__(self, rate: float | Decimal) -> None:
        rate = Decimal(str(rate))
        if not (Decimal("0") <= rate <= Decimal("1")):
            raise ValueError(f"TaxRate must be between 0 and 1, got {rate}")
        object.__setattr__(self, "_rate", rate)

    @property
    def rate(self) -> Decimal:
        return self._rate

    def as_float(self) -> float:
        return float(self._rate)

    def as_percentage(self) -> Decimal:
        return self._rate * Decimal("100")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("TaxRate is immutable")

    def __repr__(self) -> str:
        return f"TaxRate({float(self._rate)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaxRate):
            return False
        return self._rate == other._rate

    def __hash__(self) -> int:
        return hash((self.__class__, self._rate))
