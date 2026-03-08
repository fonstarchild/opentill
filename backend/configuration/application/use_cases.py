from __future__ import annotations
from typing import List, Optional
from ..domain.shop_config import ShopConfig
from ..domain.value_objects import CurrencyCode, ReceiptSettings, ShopInfo
from ..infrastructure.json_repository import JsonConfigRepository


class GetConfig:
    def __init__(self, repo: JsonConfigRepository) -> None:
        self._repo = repo

    def execute(self) -> ShopConfig:
        return self._repo.load()


class UpdateConfig:
    def __init__(self, repo: JsonConfigRepository) -> None:
        self._repo = repo

    def execute(self, data: dict) -> ShopConfig:
        config = self._repo.load()
        if "shop" in data:
            s = data["shop"]
            config.update_shop(ShopInfo(
                name=s.get("name", config.shop.name),
                address=s.get("address", config.shop.address),
                phone=s.get("phone", config.shop.phone),
                tax_id=s.get("tax_id", config.shop.tax_id),
                website=s.get("website", config.shop.website),
                receipt_footer=s.get("receipt_footer", config.shop.receipt_footer),
            ))
        if "currency" in data:
            config.update_currency(CurrencyCode(data["currency"]))
        if "locale" in data:
            config.locale = data["locale"]
        if "receipt" in data:
            r = data["receipt"]
            config.update_receipt(ReceiptSettings(
                paper_width_mm=r.get("paper_width_mm", config.receipt.paper_width_mm),
                show_vat_breakdown=r.get("show_vat_breakdown", config.receipt.show_vat_breakdown),
                logo_url=r.get("logo_url", config.receipt.logo_url),
            ))
        self._repo.save(config)
        return config


class UpdatePaymentMethods:
    def __init__(self, repo: JsonConfigRepository) -> None:
        self._repo = repo

    def execute(self, active: Optional[List[str]] = None, configs: Optional[dict] = None) -> ShopConfig:
        config = self._repo.load()
        config.update_payment_methods(active=active, configs=configs)
        self._repo.save(config)
        return config
