from __future__ import annotations
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from backend.shared.domain.value_object import Money, Barcode, SKU, TaxRate
from ..domain.product import Product
from ..domain.repository import IProductRepository
from .sqlmodel_models import ProductTable


def _to_domain(row: ProductTable) -> Product:
    barcode = Barcode(row.barcode) if row.barcode else None
    return Product(
        id=row.id,
        sku=SKU(row.sku),
        name=row.name,
        price=Money(Decimal(str(row.price)), row.currency),
        tax_rate=TaxRate(row.tax_rate),
        stock=row.stock,
        barcode=barcode,
        cost=Money(Decimal(str(row.cost)), row.currency),
        category=row.category,
        description=row.description,
        active=row.active,
    )


def _to_row(product: Product, existing: Optional[ProductTable] = None) -> ProductTable:
    row = existing or ProductTable()
    row.name = product.name
    row.sku = product.sku.value
    row.barcode = product.barcode.value if product.barcode else ""
    row.price = product.price.as_float()
    row.cost = product.cost.as_float()
    row.tax_rate = product.tax_rate.as_float()
    row.stock = product.stock
    row.category = product.category
    row.description = product.description
    row.active = product.active
    row.currency = product.price.currency
    if product.id is not None:
        row.id = product.id
    return row


class SqlModelProductRepository(IProductRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, id: int) -> Optional[Product]:
        row = self._session.get(ProductTable, id)
        return _to_domain(row) if row else None

    def get_by_sku(self, sku: SKU) -> Optional[Product]:
        row = self._session.exec(
            select(ProductTable).where(ProductTable.sku == sku.value)
        ).first()
        return _to_domain(row) if row else None

    def get_by_barcode(self, barcode: Barcode) -> Optional[Product]:
        row = self._session.exec(
            select(ProductTable).where(ProductTable.barcode == barcode.value)
        ).first()
        return _to_domain(row) if row else None

    def save(self, product: Product) -> Product:
        if product.id is not None:
            existing = self._session.get(ProductTable, product.id)
            row = _to_row(product, existing)
        else:
            row = _to_row(product)

        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_domain(row)

    def delete(self, id: int) -> None:
        row = self._session.get(ProductTable, id)
        if row:
            self._session.delete(row)
            self._session.commit()

    def list(self) -> list[Product]:
        rows = self._session.exec(
            select(ProductTable).where(ProductTable.active == True)
        ).all()
        return [_to_domain(r) for r in rows]

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        in_stock: bool = False,
        sku: Optional[str] = None,
        barcode: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Product]:
        q = select(ProductTable).where(ProductTable.active == True)
        if query:
            q = q.where(ProductTable.name.contains(query))
        if category:
            q = q.where(ProductTable.category == category)
        if in_stock:
            q = q.where(ProductTable.stock > 0)
        if sku:
            q = q.where(ProductTable.sku == sku)
        if barcode:
            q = q.where(ProductTable.barcode == barcode)
        q = q.offset((page - 1) * page_size).limit(page_size)
        return [_to_domain(r) for r in self._session.exec(q).all()]

    def list_categories(self) -> list[str]:
        results = self._session.exec(
            select(ProductTable.category)
            .where(ProductTable.active == True)
            .distinct()
        ).all()
        return [r for r in results if r]
