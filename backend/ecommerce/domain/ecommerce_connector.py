from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from backend.payments.domain.payment_provider import ConfigField
from .dtos import ExternalProduct, ExternalOrder, SyncResult


class IEcommerceConnector(ABC):
    """Interface for all ecommerce platform connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def config_schema(self) -> list[ConfigField]:
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify credentials and connectivity."""
        ...

    @abstractmethod
    def list_products(self, page: int = 1, limit: int = 50) -> list[ExternalProduct]:
        """List products from the external platform."""
        ...

    @abstractmethod
    def get_product(self, external_id: str) -> Optional[ExternalProduct]:
        """Get a single product by its external ID."""
        ...

    @abstractmethod
    def sync_product(self, product: ExternalProduct) -> SyncResult:
        """Push a product (create or update) to the external platform."""
        ...

    @abstractmethod
    def list_orders(self, since: Optional[datetime] = None) -> list[ExternalOrder]:
        """List orders from the external platform, optionally filtered by date."""
        ...

    @abstractmethod
    def update_stock(self, external_id: str, quantity: int) -> bool:
        """Update stock level for a product on the external platform."""
        ...
