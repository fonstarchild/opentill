from typing import Dict, Type
from ..domain.ecommerce_connector import IEcommerceConnector
from .connectors.woocommerce import WooCommerceConnector
from .connectors.shopify import ShopifyConnector
from .connectors.prestashop import PrestaShopConnector


CONNECTORS: Dict[str, Type[IEcommerceConnector]] = {
    "woocommerce": WooCommerceConnector,
    "shopify": ShopifyConnector,
    "prestashop": PrestaShopConnector,
}


def get_connector(name: str, config: dict) -> IEcommerceConnector:
    cls = CONNECTORS.get(name.lower())
    if not cls:
        from ..domain.exceptions import ConnectorNotFoundError
        raise ConnectorNotFoundError(f"Unknown ecommerce connector: {name!r}")
    return cls(config)
