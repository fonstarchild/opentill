"""FastAPI integration tests for catalog router."""
import pytest
from fastapi.testclient import TestClient


class TestProductEndpoints:
    def test_list_products_empty(self, client: TestClient):
        resp = client.get("/api/catalog/products")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_product(self, client: TestClient, sample_product_data: dict):
        resp = client.post("/api/catalog/products", json=sample_product_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["sku"] == "TEST-001"
        assert data["name"] == "Test Product"
        assert data["price"] == pytest.approx(9.99)
        assert data["stock"] == 10

    def test_get_product(self, client: TestClient, sample_product_data: dict):
        create_resp = client.post("/api/catalog/products", json=sample_product_data)
        product_id = create_resp.json()["id"]
        resp = client.get(f"/api/catalog/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == product_id

    def test_get_nonexistent_product(self, client: TestClient):
        resp = client.get("/api/catalog/products/9999")
        assert resp.status_code == 404

    def test_list_products_after_create(self, client: TestClient, sample_product_data: dict):
        client.post("/api/catalog/products", json=sample_product_data)
        resp = client.get("/api/catalog/products")
        assert len(resp.json()) == 1

    def test_update_product(self, client: TestClient, sample_product_data: dict):
        create_resp = client.post("/api/catalog/products", json=sample_product_data)
        product_id = create_resp.json()["id"]
        resp = client.patch(
            f"/api/catalog/products/{product_id}",
            json={"name": "Updated Name", "price": 19.99},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["price"] == pytest.approx(19.99)

    def test_adjust_stock(self, client: TestClient, sample_product_data: dict):
        create_resp = client.post("/api/catalog/products", json=sample_product_data)
        product_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/catalog/products/{product_id}/stock",
            json={"delta": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["stock"] == 15

    def test_adjust_stock_below_zero(self, client: TestClient, sample_product_data: dict):
        create_resp = client.post("/api/catalog/products", json=sample_product_data)
        product_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/catalog/products/{product_id}/stock",
            json={"delta": -100},
        )
        assert resp.status_code == 400

    def test_delete_product_soft(self, client: TestClient, sample_product_data: dict):
        create_resp = client.post("/api/catalog/products", json=sample_product_data)
        product_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/catalog/products/{product_id}")
        assert del_resp.status_code == 204
        # Product no longer in list (soft deleted)
        list_resp = client.get("/api/catalog/products")
        assert all(p["id"] != product_id for p in list_resp.json())

    def test_categories_endpoint(self, client: TestClient, sample_product_data: dict):
        client.post("/api/catalog/products", json=sample_product_data)
        resp = client.get("/api/catalog/categories")
        assert resp.status_code == 200
        assert "General" in resp.json()

    def test_duplicate_sku_rejected(self, client: TestClient, sample_product_data: dict):
        client.post("/api/catalog/products", json=sample_product_data)
        resp = client.post("/api/catalog/products", json=sample_product_data)
        assert resp.status_code == 409

    def test_search_by_name(self, client: TestClient, sample_product_data: dict):
        client.post("/api/catalog/products", json=sample_product_data)
        resp = client.get("/api/catalog/products?search=Test")
        assert len(resp.json()) == 1

    def test_filter_in_stock(self, client: TestClient, sample_product_data: dict):
        client.post("/api/catalog/products", json=sample_product_data)
        out_of_stock = {**sample_product_data, "sku": "NO-STOCK", "stock": 0}
        client.post("/api/catalog/products", json=out_of_stock)
        resp = client.get("/api/catalog/products?in_stock=true")
        assert all(p["stock"] > 0 for p in resp.json())
