from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.shared.domain.exceptions import DomainException
from ..application.use_cases import SyncCatalog, ImportOrders, TestConnection
from ..domain.dtos import ExternalProduct, SyncResult, ExternalOrder
from ..infrastructure.connector_registry import CONNECTORS, get_connector

router = APIRouter()


class ConnectorInfo(BaseModel):
    id: str
    name: str
    config_schema: List[dict]


class SyncRequest(BaseModel):
    connector: str
    config: dict
    products: List[dict] = []


class ImportOrdersRequest(BaseModel):
    connector: str
    config: dict
    since: Optional[datetime] = None


class ConnectionTestRequest(BaseModel):
    connector: str
    config: dict


@router.get("/connectors", response_model=List[ConnectorInfo])
def list_connectors():
    result = []
    for key, cls in CONNECTORS.items():
        instance = cls({})
        result.append(ConnectorInfo(
            id=key,
            name=instance.name,
            config_schema=[
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "required": f.required,
                    "options": f.options,
                    "help_text": f.help_text,
                }
                for f in instance.config_schema
            ],
        ))
    return result


@router.post("/test-connection")
def test_connection(request: ConnectionTestRequest):
    try:
        connector = get_connector(request.connector, request.config)
        ok = TestConnection(connector).execute()
        return {"success": ok}
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.post("/sync")
def sync_catalog(request: SyncRequest):
    try:
        connector = get_connector(request.connector, request.config)
        products = [
            ExternalProduct(
                external_id=p.get("external_id", ""),
                name=p["name"],
                sku=p.get("sku", ""),
                price=float(p.get("price", 0)),
                stock=int(p.get("stock", 0)),
                barcode=p.get("barcode", ""),
                description=p.get("description", ""),
                active=p.get("active", True),
            )
            for p in request.products
        ]
        results = SyncCatalog(connector).execute(products)
        return {
            "synced": len([r for r in results if r.success]),
            "failed": len([r for r in results if not r.success]),
            "results": [{"success": r.success, "external_id": r.external_id, "message": r.message} for r in results],
        }
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.post("/import-orders")
def import_orders(request: ImportOrdersRequest):
    try:
        connector = get_connector(request.connector, request.config)
        orders = ImportOrders(connector).execute(since=request.since)
        return {"count": len(orders), "orders": [
            {
                "external_id": o.external_id,
                "reference": o.reference,
                "status": o.status,
                "total": o.total,
                "currency": o.currency,
                "customer_email": o.customer_email,
                "items_count": len(o.items),
            }
            for o in orders
        ]}
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))
