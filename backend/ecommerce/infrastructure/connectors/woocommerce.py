"""
WooCommerce connector using WooCommerce REST API v3.

Docs: https://woocommerce.github.io/woocommerce-rest-api-docs/
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from backend.payments.domain.payment_provider import ConfigField
from backend.ecommerce.domain.ecommerce_connector import IEcommerceConnector
from backend.ecommerce.domain.dtos import ExternalProduct, ExternalOrder, ExternalOrderItem, SyncResult


class WooCommerceConnector(IEcommerceConnector):
    """WooCommerce REST API v3 connector."""

    def __init__(self, config: dict) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "WooCommerce"

    @property
    def config_schema(self) -> list[ConfigField]:
        return [
            ConfigField(key="base_url", label="Store URL", type="text", required=True,
                        help_text="e.g. https://myshop.com"),
            ConfigField(key="consumer_key", label="Consumer Key", type="text", required=True),
            ConfigField(key="consumer_secret", label="Consumer Secret", type="password", required=True),
        ]

    def _client(self):
        import requests
        from requests.auth import HTTPBasicAuth
        session = requests.Session()
        session.auth = HTTPBasicAuth(
            self._config["consumer_key"],
            self._config["consumer_secret"],
        )
        return session

    def _url(self, path: str) -> str:
        base = self._config["base_url"].rstrip("/")
        return f"{base}/wp-json/wc/v3/{path.lstrip('/')}"

    def test_connection(self) -> bool:
        try:
            resp = self._client().get(self._url("system_status"), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def list_products(self, page: int = 1, limit: int = 50) -> list[ExternalProduct]:
        resp = self._client().get(
            self._url("products"),
            params={"page": page, "per_page": limit, "status": "publish"},
            timeout=15,
        )
        resp.raise_for_status()
        results = []
        for p in resp.json():
            results.append(ExternalProduct(
                external_id=str(p["id"]),
                name=p["name"],
                sku=p.get("sku", ""),
                price=float(p.get("price", 0) or 0),
                stock=p.get("stock_quantity") or 0,
                description=p.get("short_description", ""),
                active=p.get("status") == "publish",
                raw=p,
            ))
        return results

    def get_product(self, external_id: str) -> Optional[ExternalProduct]:
        resp = self._client().get(self._url(f"products/{external_id}"), timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        p = resp.json()
        return ExternalProduct(
            external_id=str(p["id"]),
            name=p["name"],
            sku=p.get("sku", ""),
            price=float(p.get("price", 0) or 0),
            stock=p.get("stock_quantity") or 0,
            description=p.get("short_description", ""),
            active=p.get("status") == "publish",
            raw=p,
        )

    def sync_product(self, product: ExternalProduct) -> SyncResult:
        client = self._client()
        payload = {
            "name": product.name,
            "sku": product.sku,
            "regular_price": str(product.price),
            "stock_quantity": product.stock,
            "manage_stock": True,
            "status": "publish" if product.active else "draft",
        }
        # Check if product exists by SKU
        existing = client.get(
            self._url("products"),
            params={"sku": product.sku},
            timeout=10,
        )
        existing.raise_for_status()
        items = existing.json()
        if items:
            ext_id = str(items[0]["id"])
            resp = client.put(self._url(f"products/{ext_id}"), json=payload, timeout=15)
        else:
            resp = client.post(self._url("products"), json=payload, timeout=15)
        resp.raise_for_status()
        return SyncResult(success=True, external_id=str(resp.json()["id"]))

    def list_orders(self, since: Optional[datetime] = None) -> list[ExternalOrder]:
        params: dict = {"status": "any", "per_page": 100}
        if since:
            params["after"] = since.isoformat()
        resp = self._client().get(self._url("orders"), params=params, timeout=20)
        resp.raise_for_status()
        results = []
        for o in resp.json():
            items = [
                ExternalOrderItem(
                    product_id=str(i.get("product_id", "")),
                    product_name=i.get("name", ""),
                    quantity=i.get("quantity", 1),
                    unit_price=float(i.get("price", 0) or 0),
                )
                for i in o.get("line_items", [])
            ]
            billing = o.get("billing", {})
            results.append(ExternalOrder(
                external_id=str(o["id"]),
                reference=o.get("number", str(o["id"])),
                status=o.get("status", ""),
                total=float(o.get("total", 0) or 0),
                currency=o.get("currency", "EUR"),
                items=items,
                customer_name=f"{billing.get('first_name','')} {billing.get('last_name','')}".strip(),
                customer_email=billing.get("email", ""),
                created_at=datetime.fromisoformat(o["date_created"]) if o.get("date_created") else None,
                raw=o,
            ))
        return results

    def update_stock(self, external_id: str, quantity: int) -> bool:
        resp = self._client().put(
            self._url(f"products/{external_id}"),
            json={"stock_quantity": quantity, "manage_stock": True},
            timeout=10,
        )
        return resp.status_code in (200, 201)
