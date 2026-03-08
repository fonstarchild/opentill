"""
PrestaShop connector using PrestaShop REST API (WebService).

Docs: https://devdocs.prestashop-project.org/8/webservice/
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from backend.payments.domain.payment_provider import ConfigField
from backend.ecommerce.domain.ecommerce_connector import IEcommerceConnector
from backend.ecommerce.domain.dtos import ExternalProduct, ExternalOrder, ExternalOrderItem, SyncResult


class PrestaShopConnector(IEcommerceConnector):
    """PrestaShop WebService REST connector."""

    def __init__(self, config: dict) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "PrestaShop"

    @property
    def config_schema(self) -> list[ConfigField]:
        return [
            ConfigField(key="base_url", label="Shop URL", type="text", required=True,
                        help_text="e.g. https://myshop.com"),
            ConfigField(key="api_key", label="WebService API Key", type="password", required=True,
                        help_text="From Admin → Advanced → Webservice"),
        ]

    def _client(self):
        import requests
        from requests.auth import HTTPBasicAuth
        session = requests.Session()
        # PrestaShop uses API key as username, empty password
        session.auth = HTTPBasicAuth(self._config["api_key"], "")
        return session

    def _url(self, path: str) -> str:
        base = self._config["base_url"].rstrip("/")
        return f"{base}/api/{path.lstrip('/')}"

    def test_connection(self) -> bool:
        try:
            resp = self._client().get(
                self._url(""),
                params={"output_format": "JSON"},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def list_products(self, page: int = 1, limit: int = 50) -> list[ExternalProduct]:
        resp = self._client().get(
            self._url("products"),
            params={
                "output_format": "JSON",
                "limit": f"{(page-1)*limit},{limit}",
                "display": "full",
                "filter[active]": 1,
            },
            timeout=15,
        )
        resp.raise_for_status()
        products = resp.json().get("products", [])
        results = []
        for p in products:
            name = p.get("name", [{}])
            name_str = name[0].get("value", "") if isinstance(name, list) else str(name)
            results.append(ExternalProduct(
                external_id=str(p["id"]),
                name=name_str,
                sku=p.get("reference", ""),
                price=float(p.get("price", 0) or 0),
                stock=int(p.get("quantity", 0) or 0),
                active=bool(int(p.get("active", 1))),
                raw=p,
            ))
        return results

    def get_product(self, external_id: str) -> Optional[ExternalProduct]:
        resp = self._client().get(
            self._url(f"products/{external_id}"),
            params={"output_format": "JSON"},
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        p = resp.json().get("product", {})
        name = p.get("name", [{}])
        name_str = name[0].get("value", "") if isinstance(name, list) else str(name)
        return ExternalProduct(
            external_id=str(p["id"]),
            name=name_str,
            sku=p.get("reference", ""),
            price=float(p.get("price", 0) or 0),
            stock=int(p.get("quantity", 0) or 0),
            active=bool(int(p.get("active", 1))),
            raw=p,
        )

    def sync_product(self, product: ExternalProduct) -> SyncResult:
        client = self._client()
        # PrestaShop requires XML for write operations
        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <product>
    <active>{1 if product.active else 0}</active>
    <reference>{product.sku}</reference>
    <price>{product.price}</price>
    <name><language id="1">{product.name}</language></name>
    <description_short><language id="1">{product.description}</language></description_short>
  </product>
</prestashop>"""
        headers = {"Content-Type": "application/xml"}
        if product.external_id:
            resp = client.put(
                self._url(f"products/{product.external_id}"),
                data=xml_payload.encode(),
                headers=headers,
                timeout=15,
            )
        else:
            resp = client.post(
                self._url("products"),
                data=xml_payload.encode(),
                headers=headers,
                timeout=15,
            )
        resp.raise_for_status()
        return SyncResult(success=True, external_id=product.external_id or "")

    def list_orders(self, since: Optional[datetime] = None) -> list[ExternalOrder]:
        params: dict = {"output_format": "JSON", "display": "full"}
        if since:
            params["filter[date_add]"] = f">[{since.strftime('%Y-%m-%d %H:%M:%S')}]"
        resp = self._client().get(self._url("orders"), params=params, timeout=20)
        resp.raise_for_status()
        orders = resp.json().get("orders", [])
        results = []
        for o in orders:
            items = [
                ExternalOrderItem(
                    product_id=str(i.get("product_id", "")),
                    product_name=i.get("product_name", ""),
                    quantity=int(i.get("product_quantity", 1)),
                    unit_price=float(i.get("unit_price_tax_incl", 0) or 0),
                )
                for i in o.get("associations", {}).get("order_rows", [])
            ]
            results.append(ExternalOrder(
                external_id=str(o["id"]),
                reference=o.get("reference", str(o["id"])),
                status=str(o.get("current_state", "")),
                total=float(o.get("total_paid", 0) or 0),
                currency="EUR",
                items=items,
                customer_name="",
                customer_email="",
                created_at=datetime.fromisoformat(o["date_add"]) if o.get("date_add") else None,
                raw=o,
            ))
        return results

    def update_stock(self, external_id: str, quantity: int) -> bool:
        # PrestaShop manages stock via StockAvailable resource
        resp = self._client().get(
            self._url("stock_availables"),
            params={"output_format": "JSON", "filter[id_product]": external_id},
            timeout=10,
        )
        if resp.status_code != 200:
            return False
        items = resp.json().get("stock_availables", [])
        if not items:
            return False
        stock_id = items[0]["id"]
        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <stock_available>
    <id>{stock_id}</id>
    <quantity>{quantity}</quantity>
  </stock_available>
</prestashop>"""
        resp = self._client().put(
            self._url(f"stock_availables/{stock_id}"),
            data=xml_payload.encode(),
            headers={"Content-Type": "application/xml"},
            timeout=10,
        )
        return resp.status_code in (200, 201)
