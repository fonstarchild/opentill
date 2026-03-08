from backend.shared.domain.exceptions import DomainException


class PaymentProviderError(DomainException):
    """Generic payment provider failure."""
    http_status = 502


class ProviderNotConfiguredError(DomainException):
    """Provider is missing required configuration."""
    http_status = 400


class UnknownProviderError(DomainException):
    """Requested provider does not exist."""
    http_status = 400
