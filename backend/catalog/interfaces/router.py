from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from backend.database import get_session
from backend.shared.domain.exceptions import NotFoundError, DomainException
from ..application.dtos import (
    CreateProductCommand,
    UpdateProductCommand,
    AdjustStockCommand,
    SearchProductsQuery,
    ProductDTO,
)
from ..application.use_cases import (
    CreateProduct,
    UpdateProduct,
    AdjustStock,
    DeactivateProduct,
    SearchProducts,
    GetProduct,
    ListCategories,
)
from ..infrastructure.repository import SqlModelProductRepository

router = APIRouter()


def get_repo(session: Session = Depends(get_session)) -> SqlModelProductRepository:
    return SqlModelProductRepository(session)


# ── Request/Response Schemas ──────────────────────────────────────────────────

class ProductCreateRequest(BaseModel):
    name: str
    sku: str
    price: float
    tax_rate: float = 0.21
    barcode: str = ""
    cost: float = 0.0
    stock: int = 0
    category: str = ""
    description: str = ""
    currency: str = "EUR"


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    tax_rate: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    currency: str = "EUR"


class StockAdjustmentRequest(BaseModel):
    delta: int
    reason: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductDTO])
def list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    in_stock: bool = Query(False),
    sku: Optional[str] = Query(None),
    barcode: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    repo: SqlModelProductRepository = Depends(get_repo),
):
    use_case = SearchProducts(repo)
    return use_case.execute(SearchProductsQuery(
        query=search,
        category=category,
        in_stock=in_stock,
        sku=sku,
        barcode=barcode,
        page=page,
        page_size=page_size,
    ))


@router.get("/products/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, repo: SqlModelProductRepository = Depends(get_repo)):
    try:
        return GetProduct(repo).execute(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/products", response_model=ProductDTO, status_code=201)
def create_product(
    data: ProductCreateRequest,
    repo: SqlModelProductRepository = Depends(get_repo),
):
    try:
        cmd = CreateProductCommand(
            name=data.name,
            sku=data.sku,
            price=data.price,
            tax_rate=data.tax_rate,
            barcode=data.barcode,
            cost=data.cost,
            stock=data.stock,
            category=data.category,
            description=data.description,
            currency=data.currency,
        )
        return CreateProduct(repo).execute(cmd)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.patch("/products/{product_id}", response_model=ProductDTO)
def update_product(
    product_id: int,
    data: ProductUpdateRequest,
    repo: SqlModelProductRepository = Depends(get_repo),
):
    try:
        cmd = UpdateProductCommand(
            product_id=product_id,
            name=data.name,
            price=data.price,
            cost=data.cost,
            tax_rate=data.tax_rate,
            category=data.category,
            description=data.description,
            active=data.active,
            currency=data.currency,
        )
        return UpdateProduct(repo).execute(cmd)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.post("/products/{product_id}/stock", response_model=ProductDTO)
def adjust_stock(
    product_id: int,
    adjustment: StockAdjustmentRequest,
    repo: SqlModelProductRepository = Depends(get_repo),
):
    try:
        cmd = AdjustStockCommand(
            product_id=product_id,
            delta=adjustment.delta,
            reason=adjustment.reason,
        )
        return AdjustStock(repo).execute(cmd)
    except DomainException as e:
        raise HTTPException(status_code=e.http_status, detail=str(e))


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    repo: SqlModelProductRepository = Depends(get_repo),
):
    try:
        DeactivateProduct(repo).execute(product_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/categories", response_model=List[str])
def list_categories(repo: SqlModelProductRepository = Depends(get_repo)):
    return ListCategories(repo).execute()
