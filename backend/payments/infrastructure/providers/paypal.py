"""
PayPal payment provider.

Uses PayPal Orders API v2 for in-person or online payments.
Requires a PayPal Business account and REST API credentials.

Docs: https://developer.paypal.com/docs/api/orders/v2/
"""
import uuid
from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class PayPalProvider(IPaymentProvider):
    id = "PAYPAL"
    name = "PayPal"
    requires_network = True

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="client_id",
                label="PayPal Client ID",
                type="text",
                required=True,
                help_text="From PayPal Developer Dashboard → Apps & Credentials",
            ),
            ConfigField(
                key="client_secret",
                label="PayPal Client Secret",
                type="password",
                required=True,
                help_text="From PayPal Developer Dashboard → Apps & Credentials",
            ),
            ConfigField(
                key="mode",
                label="Mode",
                type="select",
                required=False,
                options=["sandbox", "live"],
                help_text="Use 'sandbox' for testing, 'live' for production",
            ),
        ]

    def _get_access_token(self) -> str:
        import requests
        import base64
        mode = self.config.get("mode", "sandbox")
        base_url = "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"
        credentials = base64.b64encode(
            f"{self.config['client_id']}:{self.config['client_secret']}".encode()
        ).decode()
        resp = requests.post(
            f"{base_url}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data="grant_type=client_credentials",
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        try:
            import requests
            mode = self.config.get("mode", "sandbox")
            base_url = "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"
            token = self._get_access_token()
            order_ref = metadata.get("order_reference", f"OT-{uuid.uuid4().hex[:8].upper()}")

            resp = requests.post(
                f"{base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "reference_id": order_ref,
                        "amount": {
                            "currency_code": currency.upper(),
                            "value": f"{amount:.2f}",
                        },
                    }],
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
                transaction_id=data.get("id", order_ref),
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
