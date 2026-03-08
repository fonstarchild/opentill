"""
Payment provider plugin interface.

To add a new payment provider:
1. Create a file in backend/payments/providers/
2. Implement the PaymentProvider class
3. Register it in backend/payments/registry.py

The provider receives the amount and returns a PaymentResult.
For physical terminals (SumUp, Stripe Terminal) the charge() method
should initiate the terminal and wait for the result.
For manual methods (Cash, TPV) it returns success immediately.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class PaymentResult:
    success: bool
    provider: str
    amount: float
    currency: str
    transaction_id: str = ""
    error_message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigField:
    """Describes a configuration field shown in the Settings UI."""
    key: str
    label: str
    type: str = "text"       # text | password | number | boolean | select
    required: bool = False
    options: list = field(default_factory=list)   # for select type
    help_text: str = ""


class PaymentProvider(ABC):
    """Base class for all payment providers."""

    #: Unique identifier used in orders and config (e.g. "cash", "sumup")
    id: str

    #: Human-readable name shown in the UI
    name: str

    #: Whether this provider requires network/hardware (shown as offline-capable if False)
    requires_network: bool = False

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> list[ConfigField]:
        """Return the list of config fields this provider needs."""
        ...

    @abstractmethod
    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        """
        Initiate a charge.
        For terminal providers, this blocks until the customer pays or it times out.
        """
        ...

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        """Optional: initiate a refund. Not all providers support this."""
        return PaymentResult(
            success=False,
            provider=self.id,
            amount=amount,
            currency="",
            error_message="Refunds not supported by this provider",
        )

    def is_configured(self) -> bool:
        """Return True if all required config fields are present."""
        for field in self.get_config_schema():
            if field.required and not self.config.get(field.key):
                return False
        return True
