from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session
from .models import Product, ProductCreate, ProductUpdate, StockAdjustment

router = APIRouter()


@router.get("/products", response_model=List[Product])
def list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    in_stock: bool = Query(False),
    sku: Optional[str] = Query(None),
    barcode: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    session: Session = Depends(get_session),
):
    q = select(Product).where(Product.active == True)
    if search:
        q = q.where(Product.name.contains(search))
    if category:
        q = q.where(Product.category == category)
    if in_stock:
        q = q.where(Product.stock > 0)
    if sku:
        q = q.where(Product.sku == sku)
    if barcode:
        q = q.where(Product.barcode == barcode)
    q = q.offset((page - 1) * page_size).limit(page_size)
    return session.exec(q).all()


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", response_model=Product, status_code=201)
def create_product(data: ProductCreate, session: Session = Depends(get_session)):
    product = Product.model_validate(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = data.model_dump(exclude_unset=True)
    product.sqlmodel_update(update_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.post("/products/{product_id}/stock", response_model=Product)
def adjust_stock(
    product_id: int,
    adjustment: StockAdjustment,
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    new_stock = product.stock + adjustment.delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    product.stock = new_stock
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.active = False  # Soft delete
    session.add(product)
    session.commit()


@router.get("/categories", response_model=List[str])
def list_categories(session: Session = Depends(get_session)):
    results = session.exec(
        select(Product.category).where(Product.active == True).distinct()
    ).all()
    return [r for r in results if r]
