"""
Payment provider plugin interface (DDD domain layer).
Providers live in infrastructure/providers/ and implement IPaymentProvider.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ConfigField:
    """Describes a configuration field shown in the Settings UI."""
    key: str
    label: str
    type: str = "text"       # text | password | number | boolean | select
    required: bool = False
    options: list = field(default_factory=list)
    help_text: str = ""


@dataclass
class PaymentResult:
    """Value object representing the outcome of a payment attempt."""
    success: bool
    provider: str
    amount: float
    currency: str
    transaction_id: str = ""
    error_message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


class IPaymentProvider(ABC):
    """Interface for all payment providers."""

    id: str
    name: str
    requires_network: bool = False

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> list[ConfigField]:
        ...

    @abstractmethod
    def charge(self, amount: float, currency: str, metadata: Dict[str, Any]) -> PaymentResult:
        ...

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        return PaymentResult(
            success=False,
            provider=self.id,
            amount=amount,
            currency="",
            error_message="Refunds not supported by this provider",
        )

    def is_configured(self) -> bool:
        for f in self.get_config_schema():
            if f.required and not self.config.get(f.key):
                return False
        return True
