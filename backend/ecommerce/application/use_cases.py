from __future__ import annotations
from datetime import datetime
from typing import Optional

from ..domain.ecommerce_connector import IEcommerceConnector
from ..domain.dtos import ExternalProduct, SyncResult
from ..domain.exceptions import SyncError


class SyncCatalog:
    """Push all local products to the external platform."""

    def __init__(self, connector: IEcommerceConnector) -> None:
        self._connector = connector

    def execute(self, products: list[ExternalProduct]) -> list[SyncResult]:
        results = []
        for product in products:
            try:
                result = self._connector.sync_product(product)
            except Exception as e:
                result = SyncResult(success=False, message=str(e))
            results.append(result)
        return results


class ImportOrders:
    """Pull orders from the external platform since a given date."""

    def __init__(self, connector: IEcommerceConnector) -> None:
        self._connector = connector

    def execute(self, since: Optional[datetime] = None):
        return self._connector.list_orders(since=since)


class TestConnection:
    def __init__(self, connector: IEcommerceConnector) -> None:
        self._connector = connector

    def execute(self) -> bool:
        try:
            return self._connector.test_connection()
        except Exception:
            return False
