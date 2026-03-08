from __future__ import annotations
from decimal import Decimal
from typing import Optional

from backend.shared.domain.value_object import Money, Barcode, SKU, TaxRate
from backend.shared.domain.exceptions import NotFoundError
from ..domain.product import Product
from ..domain.repository import IProductRepository
from ..domain.exceptions import DuplicateSKUError, DuplicateBarcodeError
from .dtos import (
    CreateProductCommand,
    UpdateProductCommand,
    AdjustStockCommand,
    SearchProductsQuery,
    ProductDTO,
)


def _to_dto(product: Product) -> ProductDTO:
    return ProductDTO(
        id=product.id,
        name=product.name,
        sku=product.sku.value,
        price=product.price.as_float(),
        tax_rate=product.tax_rate.as_float(),
        stock=product.stock,
        barcode=product.barcode.value if product.barcode else "",
        cost=product.cost.as_float(),
        category=product.category,
        description=product.description,
        active=product.active,
        currency=product.price.currency,
    )


class CreateProduct:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, cmd: CreateProductCommand) -> ProductDTO:
        sku = SKU(cmd.sku)
        if self._repo.get_by_sku(sku):
            raise DuplicateSKUError(f"SKU already exists: {cmd.sku!r}")

        barcode = None
        if cmd.barcode:
            barcode = Barcode(cmd.barcode)
            if self._repo.get_by_barcode(barcode):
                raise DuplicateBarcodeError(f"Barcode already exists: {cmd.barcode!r}")

        product = Product.create(
            sku=sku,
            name=cmd.name,
            price=Money(Decimal(str(cmd.price)), cmd.currency),
            tax_rate=TaxRate(cmd.tax_rate),
            stock=cmd.stock,
            barcode=barcode,
            cost=Money(Decimal(str(cmd.cost)), cmd.currency),
            category=cmd.category,
            description=cmd.description,
        )
        saved = self._repo.save(product)
        return _to_dto(saved)


class UpdateProduct:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, cmd: UpdateProductCommand) -> ProductDTO:
        product = self._repo.get(cmd.product_id)
        if not product:
            raise NotFoundError(f"Product not found: {cmd.product_id}")

        price = Money(Decimal(str(cmd.price)), cmd.currency) if cmd.price is not None else None
        cost = Money(Decimal(str(cmd.cost)), cmd.currency) if cmd.cost is not None else None
        tax_rate = TaxRate(cmd.tax_rate) if cmd.tax_rate is not None else None

        product.update(
            name=cmd.name,
            price=price,
            cost=cost,
            tax_rate=tax_rate,
            category=cmd.category,
            description=cmd.description,
            active=cmd.active,
        )
        saved = self._repo.save(product)
        return _to_dto(saved)


class AdjustStock:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, cmd: AdjustStockCommand) -> ProductDTO:
        product = self._repo.get(cmd.product_id)
        if not product:
            raise NotFoundError(f"Product not found: {cmd.product_id}")
        product.adjust_stock(cmd.delta, cmd.reason)
        saved = self._repo.save(product)
        return _to_dto(saved)


class DeactivateProduct:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, product_id: int) -> None:
        product = self._repo.get(product_id)
        if not product:
            raise NotFoundError(f"Product not found: {product_id}")
        product.deactivate()
        self._repo.save(product)


class SearchProducts:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, query: SearchProductsQuery) -> list[ProductDTO]:
        products = self._repo.search(
            query=query.query,
            category=query.category,
            in_stock=query.in_stock,
            sku=query.sku,
            barcode=query.barcode,
            page=query.page,
            page_size=query.page_size,
        )
        return [_to_dto(p) for p in products]


class GetProduct:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self, product_id: int) -> ProductDTO:
        product = self._repo.get(product_id)
        if not product:
            raise NotFoundError(f"Product not found: {product_id}")
        return _to_dto(product)


class ListCategories:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def execute(self) -> list[str]:
        return self._repo.list_categories()
