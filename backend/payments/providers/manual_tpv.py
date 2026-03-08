"""
Manual TPV / Card reader provider.

For businesses that have a standalone card terminal not connected to the API.
The cashier processes the payment on the physical terminal and then confirms
in Opentill. No network calls — always succeeds when confirmed by operator.
"""
import uuid
from typing import Dict, Any

from ..base import PaymentProvider, PaymentResult, ConfigField


class ManualTPVProvider(PaymentProvider):
    id = "TPV"
    name = "Card (Manual TPV)"
    requires_network = False

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return []

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        return PaymentResult(
            success=True,
            provider=self.id,
            amount=amount,
            currency=currency,
            transaction_id=f"tpv-{uuid.uuid4().hex[:8]}",
        )
