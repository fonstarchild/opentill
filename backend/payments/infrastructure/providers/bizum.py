import uuid
from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class BizumProvider(IPaymentProvider):
    id = "BIZUM"
    name = "Bizum"
    requires_network = False

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="phone",
                label="Business phone number",
                type="text",
                required=False,
                help_text="Shown on the receipt so the customer knows where to send the Bizum",
            ),
        ]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        return PaymentResult(
            success=True,
            provider=self.id,
            amount=amount,
            currency=currency,
            transaction_id=f"bizum-{uuid.uuid4().hex[:8]}",
        )
