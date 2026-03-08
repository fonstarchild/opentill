"""Tests for payment providers."""
import pytest
from backend.payments.infrastructure.providers.cash import CashProvider
from backend.payments.infrastructure.providers.manual_tpv import ManualTPVProvider
from backend.payments.infrastructure.providers.bizum import BizumProvider
from backend.payments.domain.payment_provider import PaymentResult


class TestCashProvider:
    def setup_method(self):
        self.provider = CashProvider({})

    def test_charge_returns_success(self):
        result = self.provider.charge(10.00, "EUR", {})
        assert result.success is True
        assert result.provider == "CASH"
        assert result.amount == 10.00
        assert result.currency == "EUR"
        assert result.transaction_id.startswith("cash-")

    def test_no_config_needed(self):
        assert self.provider.get_config_schema() == []

    def test_is_configured_with_empty_config(self):
        assert self.provider.is_configured() is True

    def test_not_requires_network(self):
        assert self.provider.requires_network is False


class TestManualTPVProvider:
    def setup_method(self):
        self.provider = ManualTPVProvider({})

    def test_charge_returns_success(self):
        result = self.provider.charge(25.50, "EUR", {})
        assert result.success is True
        assert result.provider == "TPV"
        assert result.transaction_id.startswith("tpv-")

    def test_no_config_needed(self):
        assert self.provider.get_config_schema() == []


class TestBizumProvider:
    def setup_method(self):
        self.provider = BizumProvider({"phone": "+34600000000"})

    def test_charge_returns_success(self):
        result = self.provider.charge(15.00, "EUR", {})
        assert result.success is True
        assert result.provider == "BIZUM"
        assert result.transaction_id.startswith("bizum-")

    def test_has_phone_config_field(self):
        schema = self.provider.get_config_schema()
        assert any(f.key == "phone" for f in schema)

    def test_not_requires_network(self):
        assert self.provider.requires_network is False


class TestPaymentsRouter:
    def test_list_providers(self, client):
        resp = client.get("/api/payments/providers")
        assert resp.status_code == 200
        providers = resp.json()
        provider_ids = [p["id"] for p in providers]
        assert "CASH" in provider_ids
        assert "TPV" in provider_ids
        assert "BIZUM" in provider_ids

    def test_charge_cash(self, client):
        resp = client.post("/api/payments/charge", json={
            "provider_id": "CASH",
            "amount": 10.00,
            "currency": "EUR",
            "config": {},
            "metadata": {},
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_charge_unknown_provider(self, client):
        resp = client.post("/api/payments/charge", json={
            "provider_id": "UNKNOWN",
            "amount": 10.00,
            "currency": "EUR",
            "config": {},
        })
        assert resp.status_code == 400

    def test_providers_have_config_schema(self, client):
        resp = client.get("/api/payments/providers")
        for provider in resp.json():
            assert "config_schema" in provider
            assert isinstance(provider["config_schema"], list)
