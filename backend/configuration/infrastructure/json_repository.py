import json
import os
from pathlib import Path
from ..domain.shop_config import ShopConfig
from ..domain.value_objects import CurrencyCode, ReceiptSettings, ShopInfo

CONFIG_PATH = Path(os.environ.get("OPENTILL_CONFIG_PATH", "opentill.config.json"))

DEFAULT_DATA = {
    "shop": {
        "name": "My Shop",
        "address": "",
        "phone": "",
        "tax_id": "",
        "website": "",
        "receipt_footer": "Thank you for your purchase!",
    },
    "currency": "EUR",
    "locale": "en-US",
    "receipt": {
        "paper_width_mm": 80,
        "show_vat_breakdown": True,
        "logo_url": "",
    },
    "active_payment_methods": ["CASH"],
    "payment_configs": {},
}


class JsonConfigRepository:
    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self._path = path

    def _read_raw(self) -> dict:
        if self._path.exists():
            try:
                return {**DEFAULT_DATA, **json.loads(self._path.read_text())}
            except Exception:
                pass
        return DEFAULT_DATA.copy()

    def load(self) -> ShopConfig:
        data = self._read_raw()
        shop_data = data.get("shop", {})
        receipt_data = data.get("receipt", {})
        return ShopConfig(
            shop=ShopInfo(
                name=shop_data.get("name", "My Shop"),
                address=shop_data.get("address", ""),
                phone=shop_data.get("phone", ""),
                tax_id=shop_data.get("tax_id", ""),
                website=shop_data.get("website", ""),
                receipt_footer=shop_data.get("receipt_footer", "Thank you for your purchase!"),
            ),
            currency=CurrencyCode(data.get("currency", "EUR")),
            locale=data.get("locale", "en-US"),
            receipt=ReceiptSettings(
                paper_width_mm=receipt_data.get("paper_width_mm", 80),
                show_vat_breakdown=receipt_data.get("show_vat_breakdown", True),
                logo_url=receipt_data.get("logo_url", ""),
            ),
            active_payment_methods=data.get("active_payment_methods", ["CASH"]),
            payment_configs=data.get("payment_configs", {}),
        )

    def save(self, config: ShopConfig) -> None:
        data = {
            "shop": {
                "name": config.shop.name,
                "address": config.shop.address,
                "phone": config.shop.phone,
                "tax_id": config.shop.tax_id,
                "website": config.shop.website,
                "receipt_footer": config.shop.receipt_footer,
            },
            "currency": config.currency.code,
            "locale": config.locale,
            "receipt": {
                "paper_width_mm": config.receipt.paper_width_mm,
                "show_vat_breakdown": config.receipt.show_vat_breakdown,
                "logo_url": config.receipt.logo_url,
            },
            "active_payment_methods": config.active_payment_methods,
            "payment_configs": config.payment_configs,
        }
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
