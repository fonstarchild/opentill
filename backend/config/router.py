"""
Shop configuration — persisted in opentill.config.json next to the database.
Readable and writable via the Settings page in the UI.
"""
import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

CONFIG_PATH = Path(os.environ.get("OPENTILL_CONFIG_PATH", "opentill.config.json"))

DEFAULT_CONFIG = {
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


def _read_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_PATH.read_text())}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def _write_config(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False))


class ShopConfig(BaseModel):
    name: str = "My Shop"
    address: str = ""
    phone: str = ""
    tax_id: str = ""
    website: str = ""
    receipt_footer: str = "Thank you for your purchase!"


class ReceiptConfig(BaseModel):
    paper_width_mm: int = 80
    show_vat_breakdown: bool = True
    logo_url: str = ""


class AppConfig(BaseModel):
    shop: ShopConfig = ShopConfig()
    currency: str = "EUR"
    locale: str = "en-US"
    receipt: ReceiptConfig = ReceiptConfig()
    active_payment_methods: List[str] = ["CASH"]
    payment_configs: dict = {}


@router.get("/", response_model=AppConfig)
def get_config():
    return _read_config()


@router.put("/", response_model=AppConfig)
def update_config(config: AppConfig):
    _write_config(config.model_dump())
    return config


@router.patch("/payment-methods", response_model=AppConfig)
def update_payment_methods(body: dict):
    config = _read_config()
    if "active" in body:
        config["active_payment_methods"] = body["active"]
    if "configs" in body:
        config["payment_configs"] = {**config.get("payment_configs", {}), **body["configs"]}
    _write_config(config)
    return config
