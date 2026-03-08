"""
Square payment provider (stub).

Implements the full IPaymentProvider interface for Square Payments API.
Requires a Square Developer account and a compatible Square Reader.

Docs: https://developer.squareup.com/docs/payments-api/overview
"""
import uuid
from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class SquareProvider(IPaymentProvider):
    id = "SQUARE"
    name = "Square"
    requires_network = True

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="access_token",
                label="Square Access Token",
                type="password",
                required=True,
                help_text="From Square Developer Dashboard → Applications → Access token",
            ),
            ConfigField(
                key="location_id",
                label="Location ID",
                type="text",
                required=True,
                help_text="Your Square location ID",
            ),
            ConfigField(
                key="device_id",
                label="Device Code / Reader ID",
                type="text",
                required=False,
                help_text="Terminal device ID for in-person payments",
            ),
            ConfigField(
                key="environment",
                label="Environment",
                type="select",
                required=False,
                options=["sandbox", "production"],
                help_text="Use 'sandbox' for testing",
            ),
        ]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        try:
            import requests
            env = self.config.get("environment", "sandbox")
            base_url = (
                "https://connect.squareup.com"
                if env == "production"
                else "https://connect.squareupsandbox.com"
            )
            idempotency_key = str(uuid.uuid4())
            order_ref = metadata.get("order_reference", idempotency_key)

            body: Dict[str, Any] = {
                "idempotency_key": idempotency_key,
                "amount_money": {
                    "amount": int(round(amount * 100)),
                    "currency": currency.upper(),
                },
                "location_id": self.config["location_id"],
                "reference_id": order_ref,
                "note": f"Opentill order {order_ref}",
            }

            # Use Terminal API if device_id is provided
            if self.config.get("device_id"):
                body["device_id"] = self.config["device_id"]
                endpoint = f"{base_url}/v2/terminals/checkouts"
                payload = {"idempotency_key": idempotency_key, "checkout": body}
            else:
                # Fall back to Payments API (requires source_id from frontend)
                endpoint = f"{base_url}/v2/payments"
                body["source_id"] = "EXTERNAL"
                body["external_details"] = {"type": "CARD", "source": "Opentill"}
                payload = body

            resp = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.config['access_token']}",
                    "Content-Type": "application/json",
                    "Square-Version": "2024-01-18",
                },
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            # Extract transaction ID from response
            tx_id = (
                data.get("payment", {}).get("id")
                or data.get("checkout", {}).get("id")
                or order_ref
            )
            return PaymentResult(
                success=True,
                provider=self.id,
                amount=amount,
                currency=currency,
                transaction_id=tx_id,
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
