from __future__ import annotations
from dataclasses import dataclass
from backend.shared.domain.value_object import ValueObject


@dataclass(frozen=True)
class CurrencyCode(ValueObject):
    code: str

    def __post_init__(self):
        if len(self.code) != 3:
            raise ValueError(f"Currency code must be 3 letters: {self.code!r}")
        object.__setattr__(self, "code", self.code.upper())


@dataclass(frozen=True)
class ReceiptSettings(ValueObject):
    paper_width_mm: int = 80
    show_vat_breakdown: bool = True
    logo_url: str = ""


@dataclass(frozen=True)
class ShopInfo(ValueObject):
    name: str = "My Shop"
    address: str = ""
    phone: str = ""
    tax_id: str = ""
    website: str = ""
    receipt_footer: str = "Thank you for your purchase!"
