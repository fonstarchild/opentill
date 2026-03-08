from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .registry import PROVIDERS, get_provider
from .base import ConfigField

router = APIRouter()


class ProviderInfo(BaseModel):
    id: str
    name: str
    requires_network: bool
    config_schema: List[dict]


class ChargeRequest(BaseModel):
    provider_id: str
    amount: float
    currency: str = "EUR"
    config: dict = {}
    metadata: dict = {}


class ChargeResponse(BaseModel):
    success: bool
    provider: str
    amount: float
    currency: str
    transaction_id: str = ""
    error_message: str = ""


@router.get("/providers", response_model=List[ProviderInfo])
def list_providers():
    """Return all available payment providers and their config schemas."""
    return [
        ProviderInfo(
            id=cls.id,
            name=cls.name,
            requires_network=cls.requires_network,
            config_schema=[
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "required": f.required,
                    "options": f.options,
                    "help_text": f.help_text,
                }
                for f in cls.get_config_schema()
            ],
        )
        for cls in PROVIDERS.values()
    ]


@router.post("/charge", response_model=ChargeResponse)
def charge(request: ChargeRequest):
    """Initiate a payment charge via the specified provider."""
    try:
        provider = get_provider(request.provider_id, request.config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = provider.charge(request.amount, request.currency, request.metadata)
    return ChargeResponse(
        success=result.success,
        provider=result.provider,
        amount=result.amount,
        currency=result.currency,
        transaction_id=result.transaction_id,
        error_message=result.error_message,
    )
