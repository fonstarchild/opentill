"""
Bizum provider (manual confirmation).

Bizum doesn't have a merchant API for in-person POS use.
The cashier asks the customer to send the Bizum, confirms receipt,
then registers the payment. Similar to manual TPV.
"""
import uuid
from typing import Dict, Any

from ..base import PaymentProvider, PaymentResult, ConfigField


class BizumProvider(PaymentProvider):
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
