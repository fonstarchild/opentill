from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.shared.domain.exceptions import DomainException
from ..application.use_cases import ProcessPayment, ListAvailableProviders
from ..infrastructure.registry import PROVIDERS

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
    return ListAvailableProviders(PROVIDERS).execute()


@router.post("/charge", response_model=ChargeResponse)
def charge(request: ChargeRequest):
    try:
        result = ProcessPayment(PROVIDERS).execute(
            provider_id=request.provider_id,
            amount=request.amount,
            currency=request.currency,
            config=request.config,
            metadata=request.metadata,
        )
        return ChargeResponse(
            success=result.success,
            provider=result.provider,
            amount=result.amount,
            currency=result.currency,
            transaction_id=result.transaction_id,
            error_message=result.error_message,
        )
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))
