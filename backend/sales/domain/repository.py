from __future__ import annotations
from abc import abstractmethod
from datetime import date
from typing import Optional

from backend.shared.domain.repository import IRepository
from .order import Order


class IOrderRepository(IRepository[Order]):
    """Order repository interface."""

    @abstractmethod
    def get_by_reference(self, reference: str) -> Optional[Order]:
        ...

    @abstractmethod
    def list_by_date_range(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Order]:
        ...

    @abstractmethod
    def count_with_prefix(self, prefix: str) -> int:
        """Count orders whose reference starts with prefix (for sequence generation)."""
        ...
