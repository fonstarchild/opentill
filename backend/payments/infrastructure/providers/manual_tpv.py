import uuid
from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class ManualTPVProvider(IPaymentProvider):
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
