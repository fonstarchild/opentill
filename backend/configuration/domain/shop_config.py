from __future__ import annotations
from typing import List
from backend.shared.domain.aggregate import AggregateRoot
from .value_objects import CurrencyCode, ReceiptSettings, ShopInfo


class ShopConfig(AggregateRoot):
    """Shop configuration aggregate root."""

    def __init__(
        self,
        shop: ShopInfo,
        currency: CurrencyCode,
        locale: str,
        receipt: ReceiptSettings,
        active_payment_methods: List[str],
        payment_configs: dict,
    ) -> None:
        super().__init__(id=1)  # Singleton
        self.shop = shop
        self.currency = currency
        self.locale = locale
        self.receipt = receipt
        self.active_payment_methods = active_payment_methods
        self.payment_configs = payment_configs

    @classmethod
    def default(cls) -> "ShopConfig":
        return cls(
            shop=ShopInfo(),
            currency=CurrencyCode("EUR"),
            locale="en-US",
            receipt=ReceiptSettings(),
            active_payment_methods=["CASH"],
            payment_configs={},
        )

    def update_shop(self, shop: ShopInfo) -> None:
        self.shop = shop

    def update_receipt(self, receipt: ReceiptSettings) -> None:
        self.receipt = receipt

    def update_currency(self, currency: CurrencyCode) -> None:
        self.currency = currency

    def update_payment_methods(
        self,
        active: List[str] | None = None,
        configs: dict | None = None,
    ) -> None:
        if active is not None:
            self.active_payment_methods = active
        if configs is not None:
            self.payment_configs = {**self.payment_configs, **configs}
