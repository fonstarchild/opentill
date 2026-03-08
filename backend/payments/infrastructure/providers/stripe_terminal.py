from typing import Dict, Any
from backend.payments.domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField


class StripeTerminalProvider(IPaymentProvider):
    id = "STRIPE_TERMINAL"
    name = "Stripe Terminal"
    requires_network = True

    @classmethod
    def get_config_schema(cls) -> list[ConfigField]:
        return [
            ConfigField(
                key="secret_key",
                label="Stripe Secret Key",
                type="password",
                required=True,
                help_text="Your sk_live_... or sk_test_... key from the Stripe Dashboard",
            ),
            ConfigField(
                key="location_id",
                label="Terminal Location ID",
                type="text",
                required=True,
                help_text="tml_... ID from Stripe Dashboard → Terminal → Locations",
            ),
            ConfigField(
                key="currency",
                label="Currency",
                type="text",
                required=False,
                help_text="ISO 4217 code (default: eur)",
            ),
        ]

    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        try:
            import stripe
            stripe.api_key = self.config["secret_key"]
            currency = self.config.get("currency", currency or "eur").lower()
            intent = stripe.PaymentIntent.create(
                amount=int(round(amount * 100)),
                currency=currency,
                payment_method_types=["card_present"],
                capture_method="automatic",
                metadata=metadata,
            )
            return PaymentResult(
                success=True,
                provider=self.id,
                amount=amount,
                currency=currency,
                transaction_id=intent["id"],
                raw={"client_secret": intent["client_secret"]},
            )
        except Exception as e:
            return PaymentResult(
                success=False,
                provider=self.id,
                amount=amount,
                currency=currency,
                error_message=str(e),
            )
