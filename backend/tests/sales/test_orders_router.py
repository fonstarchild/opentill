"""FastAPI integration tests for sales/orders router."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def created_product(client: TestClient):
    resp = client.post("/api/catalog/products", json={
        "name": "Widget",
        "sku": "WIDGET-001",
        "price": 10.00,
        "tax_rate": 0.21,
        "stock": 20,
        "currency": "EUR",
    })
    assert resp.status_code == 201
    return resp.json()


class TestOrderEndpoints:
    def test_create_order(self, client: TestClient, created_product: dict):
        resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 2}],
            "payment_method": "CASH",
            "amount_received": 30.00,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert data["reference"].startswith("OT-")
        assert data["total"] == pytest.approx(20.00)
        assert data["change_given"] == pytest.approx(10.00)

    def test_create_order_deducts_stock(self, client: TestClient, created_product: dict):
        client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 3}],
            "payment_method": "CASH",
            "amount_received": 30.00,
        })
        product_resp = client.get(f"/api/catalog/products/{created_product['id']}")
        assert product_resp.json()["stock"] == 17

    def test_create_order_insufficient_stock(self, client: TestClient, created_product: dict):
        resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 100}],
            "payment_method": "CASH",
            "amount_received": 0,
        })
        assert resp.status_code == 400

    def test_create_order_nonexistent_product(self, client: TestClient):
        resp = client.post("/api/orders/", json={
            "items": [{"product_id": 9999, "quantity": 1}],
            "payment_method": "CASH",
            "amount_received": 10,
        })
        assert resp.status_code == 404

    def test_create_empty_order(self, client: TestClient):
        resp = client.post("/api/orders/", json={
            "items": [],
            "payment_method": "CASH",
            "amount_received": 0,
        })
        assert resp.status_code == 422

    def test_list_orders(self, client: TestClient, created_product: dict):
        client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 1}],
            "payment_method": "CASH",
            "amount_received": 10,
        })
        resp = client.get("/api/orders/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_order(self, client: TestClient, created_product: dict):
        create_resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 1}],
            "payment_method": "CASH",
            "amount_received": 10,
        })
        order_id = create_resp.json()["id"]
        resp = client.get(f"/api/orders/{order_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_void_order(self, client: TestClient, created_product: dict):
        create_resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 2}],
            "payment_method": "CASH",
            "amount_received": 20,
        })
        order_id = create_resp.json()["id"]
        resp = client.post(f"/api/orders/{order_id}/void")
        assert resp.status_code == 200
        assert resp.json()["status"] == "VOID"

    def test_void_restores_stock(self, client: TestClient, created_product: dict):
        product_id = created_product["id"]
        initial_stock = created_product["stock"]
        create_resp = client.post("/api/orders/", json={
            "items": [{"product_id": product_id, "quantity": 5}],
            "payment_method": "CASH",
            "amount_received": 50,
        })
        order_id = create_resp.json()["id"]
        client.post(f"/api/orders/{order_id}/void")
        product_resp = client.get(f"/api/catalog/products/{product_id}")
        assert product_resp.json()["stock"] == initial_stock

    def test_void_already_voided(self, client: TestClient, created_product: dict):
        create_resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 1}],
            "payment_method": "CASH",
            "amount_received": 10,
        })
        order_id = create_resp.json()["id"]
        client.post(f"/api/orders/{order_id}/void")
        resp = client.post(f"/api/orders/{order_id}/void")
        assert resp.status_code == 400

    def test_order_with_discount(self, client: TestClient, created_product: dict):
        resp = client.post("/api/orders/", json={
            "items": [{"product_id": created_product["id"], "quantity": 2}],
            "payment_method": "CASH",
            "discount_amount": 5.00,
            "amount_received": 20.00,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["total"] == pytest.approx(15.00)
