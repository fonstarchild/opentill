from __future__ import annotations
from typing import Any, Dict
from ..domain.payment_provider import IPaymentProvider, PaymentResult, ConfigField
from ..domain.exceptions import UnknownProviderError, ProviderNotConfiguredError


class ProcessPayment:
    def __init__(self, registry: dict) -> None:
        self._registry = registry

    def execute(
        self,
        provider_id: str,
        amount: float,
        currency: str,
        config: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> PaymentResult:
        cls = self._registry.get(provider_id)
        if not cls:
            raise UnknownProviderError(f"Unknown payment provider: {provider_id!r}")
        provider = cls(config)
        if not provider.is_configured():
            raise ProviderNotConfiguredError(
                f"Provider {provider_id!r} is missing required configuration"
            )
        return provider.charge(amount, currency, metadata)


class ListAvailableProviders:
    def __init__(self, registry: dict) -> None:
        self._registry = registry

    def execute(self) -> list[dict]:
        result = []
        for cls in self._registry.values():
            result.append({
                "id": cls.id,
                "name": cls.name,
                "requires_network": cls.requires_network,
                "config_schema": [
                    {
                        "key": f.key,
                        "label": f.label,
                        "type": f.type,
                        "required": f.required,
                        "options": f.options,
                        "help_text": f.help_text,
                    }
                    for f in cls.get_config_schema()
                ],
            })
        return result
