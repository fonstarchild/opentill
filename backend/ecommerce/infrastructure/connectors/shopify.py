"""
Shopify connector using Shopify Admin REST API 2024-01.

Docs: https://shopify.dev/docs/api/admin-rest
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from backend.payments.domain.payment_provider import ConfigField
from backend.ecommerce.domain.ecommerce_connector import IEcommerceConnector
from backend.ecommerce.domain.dtos import ExternalProduct, ExternalOrder, ExternalOrderItem, SyncResult


class ShopifyConnector(IEcommerceConnector):
    """Shopify Admin API connector."""

    API_VERSION = "2024-01"

    def __init__(self, config: dict) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "Shopify"

    @property
    def config_schema(self) -> list[ConfigField]:
        return [
            ConfigField(key="shop_domain", label="Shop Domain", type="text", required=True,
                        help_text="e.g. myshop.myshopify.com"),
            ConfigField(key="access_token", label="Admin API Access Token", type="password",
                        required=True, help_text="From Shopify Admin → Apps → Custom apps"),
        ]

    def _url(self, path: str) -> str:
        domain = self._config["shop_domain"].rstrip("/")
        return f"https://{domain}/admin/api/{self.API_VERSION}/{path.lstrip('/')}"

    def _headers(self) -> dict:
        return {
            "X-Shopify-Access-Token": self._config["access_token"],
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        try:
            import requests
            resp = requests.get(self._url("shop.json"), headers=self._headers(), timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def list_products(self, page: int = 1, limit: int = 50) -> list[ExternalProduct]:
        import requests
        resp = requests.get(
            self._url("products.json"),
            headers=self._headers(),
            params={"limit": limit, "status": "active"},
            timeout=15,
        )
        resp.raise_for_status()
        results = []
        for p in resp.json().get("products", []):
            variant = p.get("variants", [{}])[0]
            results.append(ExternalProduct(
                external_id=str(p["id"]),
                name=p["title"],
                sku=variant.get("sku", ""),
                price=float(variant.get("price", 0) or 0),
                stock=variant.get("inventory_quantity", 0) or 0,
                description=p.get("body_html", ""),
                category=p.get("product_type", ""),
                active=p.get("status") == "active",
                raw=p,
            ))
        return results

    def get_product(self, external_id: str) -> Optional[ExternalProduct]:
        import requests
        resp = requests.get(
            self._url(f"products/{external_id}.json"),
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        p = resp.json().get("product", {})
        variant = p.get("variants", [{}])[0]
        return ExternalProduct(
            external_id=str(p["id"]),
            name=p["title"],
            sku=variant.get("sku", ""),
            price=float(variant.get("price", 0) or 0),
            stock=variant.get("inventory_quantity", 0) or 0,
            description=p.get("body_html", ""),
            active=p.get("status") == "active",
            raw=p,
        )

    def sync_product(self, product: ExternalProduct) -> SyncResult:
        import requests
        payload = {
            "product": {
                "title": product.name,
                "body_html": product.description,
                "status": "active" if product.active else "draft",
                "variants": [{
                    "sku": product.sku,
                    "price": str(product.price),
                    "inventory_quantity": product.stock,
                    "inventory_management": "shopify",
                }],
            }
        }
        if product.external_id:
            resp = requests.put(
                self._url(f"products/{product.external_id}.json"),
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
        else:
            resp = requests.post(
                self._url("products.json"),
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
        resp.raise_for_status()
        ext_id = str(resp.json().get("product", {}).get("id", ""))
        return SyncResult(success=True, external_id=ext_id)

    def list_orders(self, since: Optional[datetime] = None) -> list[ExternalOrder]:
        import requests
        params: dict = {"status": "any", "limit": 250}
        if since:
            params["created_at_min"] = since.isoformat()
        resp = requests.get(
            self._url("orders.json"),
            headers=self._headers(),
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        results = []
        for o in resp.json().get("orders", []):
            items = [
                ExternalOrderItem(
                    product_id=str(i.get("product_id", "")),
                    product_name=i.get("title", ""),
                    quantity=i.get("quantity", 1),
                    unit_price=float(i.get("price", 0) or 0),
                )
                for i in o.get("line_items", [])
            ]
            results.append(ExternalOrder(
                external_id=str(o["id"]),
                reference=o.get("name", str(o["id"])),
                status=o.get("financial_status", ""),
                total=float(o.get("total_price", 0) or 0),
                currency=o.get("currency", "EUR"),
                items=items,
                customer_name=f"{o.get('customer', {}).get('first_name','')} {o.get('customer', {}).get('last_name','')}".strip(),
                customer_email=o.get("customer", {}).get("email", ""),
                created_at=datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")) if o.get("created_at") else None,
                raw=o,
            ))
        return results

    def update_stock(self, external_id: str, quantity: int) -> bool:
        import requests
        # Get variant ID first
        product = self.get_product(external_id)
        if not product:
            return False
        # Shopify requires inventory_item_id and location_id for stock updates
        # Simplified: update via variant
        resp = requests.put(
            self._url(f"products/{external_id}.json"),
            headers=self._headers(),
            json={"product": {"variants": [{"inventory_quantity": quantity}]}},
            timeout=10,
        )
        return resp.status_code in (200, 201)
