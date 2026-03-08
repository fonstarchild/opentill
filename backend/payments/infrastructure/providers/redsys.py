"""
Redsys / TPV Virtual provider.

Redsys is the main Spanish banking card processing network (BBVA, Santander, CaixaBank, etc.).
Supports integration via REST API with HMAC-SHA256 signature.

Docs: https://pagosonline.redsys.es/conexion-basica.html
"""
import base64
import hashlib
import hmac
import json
import uuid
from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class RedsysProvider(IPaymentProvider):
    id = "REDSYS"
    name = "Redsys (TPV Virtual)"
    requires_network = True

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="merchant_code",
                label="Merchant Code (Nº de Comercio)",
                type="text",
                required=True,
                help_text="Your Redsys merchant code (9 digits)",
            ),
            ConfigField(
                key="terminal",
                label="Terminal Number",
                type="text",
                required=True,
                help_text="Terminal number (e.g. 001)",
            ),
            ConfigField(
                key="secret_key",
                label="Clave Secreta SHA-256",
                type="password",
                required=True,
                help_text="Your Redsys signing key (Base64-encoded)",
            ),
            ConfigField(
                key="environment",
                label="Environment",
                type="select",
                required=False,
                options=["test", "production"],
                help_text="Use 'test' for integration testing",
            ),
            ConfigField(
                key="currency",
                label="Currency code",
                type="text",
                required=False,
                help_text="ISO 4217 numeric code (978=EUR, default)",
            ),
        ]

    def _sign(self, order_ref: str, params_b64: str, secret_key: str) -> str:
        """HMAC-SHA256 signature per Redsys spec."""
        key = base64.b64decode(secret_key)
        # Derive order-specific key
        order_key = self._encrypt_3des(key, order_ref)
        signature = hmac.new(order_key, params_b64.encode(), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def _encrypt_3des(self, key: bytes, data: str) -> bytes:
        """3DES ECB encryption for Redsys key derivation."""
        try:
            from Crypto.Cipher import DES3
            # Pad to 8-byte boundary
            padded = data.ljust(((len(data) + 7) // 8) * 8, "\x00")
            cipher = DES3.new(key, DES3.MODE_ECB)
            return cipher.encrypt(padded.encode())
        except ImportError:
            # Fallback: use raw key (less secure, for environments without pycryptodome)
            return key[:24]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        try:
            import requests
            env = self.config.get("environment", "test")
            base_url = (
                "https://sis.redsys.es/sis/rest/trataPeticionREST"
                if env == "production"
                else "https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST"
            )
            order_ref = metadata.get("order_reference", uuid.uuid4().hex[:12].upper())
            # Redsys requires amount in cents as string, no decimals
            amount_cents = str(int(round(amount * 100)))
            currency_code = self.config.get("currency", "978")  # 978 = EUR

            params = {
                "DS_MERCHANT_AMOUNT": amount_cents,
                "DS_MERCHANT_ORDER": order_ref[:12],  # max 12 chars
                "DS_MERCHANT_MERCHANTCODE": self.config["merchant_code"],
                "DS_MERCHANT_CURRENCY": currency_code,
                "DS_MERCHANT_TRANSACTIONTYPE": "0",  # Authorization
                "DS_MERCHANT_TERMINAL": self.config.get("terminal", "001"),
            }
            params_json = json.dumps(params)
            params_b64 = base64.b64encode(params_json.encode()).decode()
            signature = self._sign(order_ref[:12], params_b64, self.config["secret_key"])

            resp = requests.post(
                base_url,
                json={
                    "DS_SIGNATUREVERSION": "HMAC_SHA256_V1",
                    "DS_MERCHANT_PARAMETERS": params_b64,
                    "DS_SIGNATURE": signature,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            # Redsys returns DS_RESPONSE 0000-0099 = success
            response_code = data.get("DS_RESPONSE", "9999")
            success = int(response_code) < 100 if response_code.isdigit() else False
            return PaymentResult(
                success=success,
                provider=self.id,
                amount=amount,
                currency=currency,
                transaction_id=data.get("DS_AUTHORISATIONCODE", order_ref),
                error_message="" if success else f"Redsys code {response_code}",
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
