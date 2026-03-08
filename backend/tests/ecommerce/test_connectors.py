"""Tests for ecommerce connectors using mock HTTP."""
import pytest
from unittest.mock import patch, MagicMock
from backend.ecommerce.infrastructure.connectors.woocommerce import WooCommerceConnector
from backend.ecommerce.infrastructure.connectors.shopify import ShopifyConnector
from backend.ecommerce.infrastructure.connectors.prestashop import PrestaShopConnector
from backend.ecommerce.domain.dtos import ExternalProduct


WOOCOMMERCE_CONFIG = {
    "base_url": "https://myshop.example.com",
    "consumer_key": "ck_test",
    "consumer_secret": "cs_test",
}

SHOPIFY_CONFIG = {
    "shop_domain": "myshop.myshopify.com",
    "access_token": "shpat_test",
}

PRESTASHOP_CONFIG = {
    "base_url": "https://myshop.example.com",
    "api_key": "test_api_key",
}


class TestWooCommerceConnector:
    def test_connector_name(self):
        connector = WooCommerceConnector(WOOCOMMERCE_CONFIG)
        assert connector.name == "WooCommerce"

    def test_has_config_schema(self):
        connector = WooCommerceConnector(WOOCOMMERCE_CONFIG)
        keys = {f.key for f in connector.config_schema}
        assert {"base_url", "consumer_key", "consumer_secret"} == keys

    def test_list_products_with_mock(self):
        connector = WooCommerceConnector(WOOCOMMERCE_CONFIG)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Product 1", "sku": "P1", "price": "9.99",
             "stock_quantity": 10, "status": "publish", "short_description": ""},
        ]
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        with patch.object(connector, '_client', return_value=mock_session):
            products = connector.list_products()
        assert len(products) == 1
        assert products[0].name == "Product 1"
        assert products[0].external_id == "1"

    def test_test_connection_success(self):
        connector = WooCommerceConnector(WOOCOMMERCE_CONFIG)
        mock_response = MagicMock(status_code=200)
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        with patch.object(connector, '_client', return_value=mock_session):
            assert connector.test_connection() is True

    def test_test_connection_failure(self):
        connector = WooCommerceConnector(WOOCOMMERCE_CONFIG)
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection refused")
        with patch.object(connector, '_client', return_value=mock_session):
            assert connector.test_connection() is False


class TestShopifyConnector:
    def test_connector_name(self):
        connector = ShopifyConnector(SHOPIFY_CONFIG)
        assert connector.name == "Shopify"

    def test_has_config_schema(self):
        connector = ShopifyConnector(SHOPIFY_CONFIG)
        keys = {f.key for f in connector.config_schema}
        assert {"shop_domain", "access_token"} == keys

    def test_list_products_with_mock(self):
        connector = ShopifyConnector(SHOPIFY_CONFIG)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {"id": 123, "title": "Test Product", "status": "active",
                 "variants": [{"sku": "SKU-1", "price": "19.99", "inventory_quantity": 5}],
                 "body_html": "", "product_type": ""},
            ]
        }
        with patch("requests.get", return_value=mock_response):
            products = connector.list_products()
        assert len(products) == 1
        assert products[0].name == "Test Product"


class TestPrestaShopConnector:
    def test_connector_name(self):
        connector = PrestaShopConnector(PRESTASHOP_CONFIG)
        assert connector.name == "PrestaShop"

    def test_has_config_schema(self):
        connector = PrestaShopConnector(PRESTASHOP_CONFIG)
        keys = {f.key for f in connector.config_schema}
        assert {"base_url", "api_key"} == keys


class TestEcommerceRouter:
    def test_list_connectors(self, client):
        resp = client.get("/api/ecommerce/connectors")
        assert resp.status_code == 200
        connectors = resp.json()
        names = [c["id"] for c in connectors]
        assert "woocommerce" in names
        assert "shopify" in names
        assert "prestashop" in names

    def test_connectors_have_config_schema(self, client):
        resp = client.get("/api/ecommerce/connectors")
        for connector in resp.json():
            assert "config_schema" in connector
