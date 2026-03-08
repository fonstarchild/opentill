from __future__ import annotations
from abc import abstractmethod
from typing import Optional

from backend.shared.domain.repository import IRepository
from backend.shared.domain.value_object import Barcode, SKU
from .product import Product


class IProductRepository(IRepository[Product]):
    """Product repository interface."""

    @abstractmethod
    def get_by_sku(self, sku: SKU) -> Optional[Product]:
        ...

    @abstractmethod
    def get_by_barcode(self, barcode: Barcode) -> Optional[Product]:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def list_categories(self) -> list[str]:
        ...
