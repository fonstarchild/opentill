"""
Payment provider registry.

To add a new provider:
1. Create backend/payments/providers/your_provider.py implementing PaymentProvider
2. Import and register it here
"""
from typing import Dict, Type

from .base import PaymentProvider
from .providers.cash import CashProvider
from .providers.manual_tpv import ManualTPVProvider
from .providers.bizum import BizumProvider
from .providers.stripe_terminal import StripeTerminalProvider
from .providers.sumup import SumUpProvider

# All available providers — order determines display order in Settings
PROVIDERS: Dict[str, Type[PaymentProvider]] = {
    CashProvider.id:            CashProvider,
    ManualTPVProvider.id:       ManualTPVProvider,
    BizumProvider.id:           BizumProvider,
    StripeTerminalProvider.id:  StripeTerminalProvider,
    SumUpProvider.id:           SumUpProvider,
}


def get_provider(provider_id: str, config: dict) -> PaymentProvider:
    cls = PROVIDERS.get(provider_id)
    if not cls:
        raise ValueError(f"Unknown payment provider: {provider_id!r}")
    return cls(config)
