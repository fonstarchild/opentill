from typing import Dict, Type
from backend.payments.domain.payment_provider import IPaymentProvider
from .providers.cash import CashProvider
from .providers.manual_tpv import ManualTPVProvider
from .providers.bizum import BizumProvider
from .providers.stripe_terminal import StripeTerminalProvider
from .providers.sumup import SumUpProvider
from .providers.paypal import PayPalProvider
from .providers.redsys import RedsysProvider
from .providers.square import SquareProvider


PROVIDERS: Dict[str, Type[IPaymentProvider]] = {
    CashProvider.id:            CashProvider,
    ManualTPVProvider.id:       ManualTPVProvider,
    BizumProvider.id:           BizumProvider,
    StripeTerminalProvider.id:  StripeTerminalProvider,
    SumUpProvider.id:           SumUpProvider,
    PayPalProvider.id:          PayPalProvider,
    RedsysProvider.id:          RedsysProvider,
    SquareProvider.id:          SquareProvider,
}


def get_provider(provider_id: str, config: dict) -> IPaymentProvider:
    cls = PROVIDERS.get(provider_id)
    if not cls:
        raise ValueError(f"Unknown payment provider: {provider_id!r}")
    return cls(config)
