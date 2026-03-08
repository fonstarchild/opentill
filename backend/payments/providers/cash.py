"""
Cash payment provider.

No configuration needed. Always succeeds — the change calculation
is handled by the frontend and stored on the order.
"""
import uuid
from typing import Dict, Any

from ..base import PaymentProvider, PaymentResult, ConfigField


class CashProvider(PaymentProvider):
    id = "CASH"
    name = "Cash"
    requires_network = False

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return []  # No configuration needed

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        return PaymentResult(
            success=True,
            provider=self.id,
            amount=amount,
            currency=currency,
            transaction_id=f"cash-{uuid.uuid4().hex[:8]}",
        )
