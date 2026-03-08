from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..application.use_cases import GetConfig, UpdateConfig, UpdatePaymentMethods
from ..infrastructure.json_repository import JsonConfigRepository

router = APIRouter()


def get_repo() -> JsonConfigRepository:
    return JsonConfigRepository()


def _config_to_dict(config) -> dict:
    return {
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


class ShopConfigModel(BaseModel):
    name: str = "My Shop"
    address: str = ""
    phone: str = ""
    tax_id: str = ""
    website: str = ""
    receipt_footer: str = "Thank you for your purchase!"


class ReceiptConfigModel(BaseModel):
    paper_width_mm: int = 80
    show_vat_breakdown: bool = True
    logo_url: str = ""


class AppConfigModel(BaseModel):
    shop: ShopConfigModel = ShopConfigModel()
    currency: str = "EUR"
    locale: str = "en-US"
    receipt: ReceiptConfigModel = ReceiptConfigModel()
    active_payment_methods: List[str] = ["CASH"]
    payment_configs: dict = {}


@router.get("/", response_model=AppConfigModel)
def get_config():
    config = GetConfig(get_repo()).execute()
    return _config_to_dict(config)


@router.put("/", response_model=AppConfigModel)
def update_config(data: AppConfigModel):
    config = UpdateConfig(get_repo()).execute(data.model_dump())
    return _config_to_dict(config)


@router.patch("/payment-methods", response_model=AppConfigModel)
def update_payment_methods(body: dict):
    active = body.get("active")
    configs = body.get("configs")
    config = UpdatePaymentMethods(get_repo()).execute(active=active, configs=configs)
    return _config_to_dict(config)
