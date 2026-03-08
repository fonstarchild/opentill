"""
SumUp provider.

Uses the SumUp REST API to initiate a checkout on a paired SumUp reader.
Requires a SumUp merchant account.

Docs: https://developer.sumup.com/docs
"""
import uuid
from typing import Dict, Any

from ..base import PaymentProvider, PaymentResult, ConfigField


class SumUpProvider(PaymentProvider):
    id = "SUMUP"
    name = "SumUp"
    requires_network = True

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="api_key",
                label="SumUp API Key",
                type="password",
                required=True,
                help_text="Your SumUp API key from developer.sumup.com",
            ),
            ConfigField(
                key="merchant_code",
                label="Merchant Code",
                type="text",
                required=True,
                help_text="Your SumUp merchant code (e.g. MC12345)",
            ),
            ConfigField(
                key="currency",
                label="Currency",
                type="text",
                required=False,
                help_text="ISO 4217 code (default: EUR)",
            ),
        ]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        try:
            import requests
            currency = self.config.get("currency", currency or "EUR").upper()
            checkout_ref = f"OT-{uuid.uuid4().hex[:12].upper()}"

            resp = requests.post(
                "https://api.sumup.com/v0.1/checkouts",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
                json={
                    "checkout_reference": checkout_ref,
                    "amount": round(amount, 2),
                    "currency": currency,
                    "merchant_code": self.config["merchant_code"],
                    "description": metadata.get("order_reference", checkout_ref),
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return PaymentResult(
                success=True,
                provider=self.id,
                amount=amount,
                currency=currency,
                transaction_id=data.get("id", checkout_ref),
                raw=data,
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                provider=self.id,
                amount=amount,
                currency=currency,
                error_message=str(e),
            )
