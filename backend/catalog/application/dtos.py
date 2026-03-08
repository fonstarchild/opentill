from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CreateProductCommand:
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


@dataclass
class UpdateProductCommand:
    product_id: int
    name: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    tax_rate: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    currency: str = "EUR"


@dataclass
class AdjustStockCommand:
    product_id: int
    delta: int
    reason: str = ""


@dataclass
class SearchProductsQuery:
    query: Optional[str] = None
    category: Optional[str] = None
    in_stock: bool = False
    sku: Optional[str] = None
    barcode: Optional[str] = None
    page: int = 1
    page_size: int = 50


@dataclass
class ProductDTO:
    id: int
    name: str
    sku: str
    price: float
    tax_rate: float
    stock: int
    barcode: str = ""
    cost: float = 0.0
    category: str = ""
    description: str = ""
    active: bool = True
    currency: str = "EUR"
