from backend.shared.domain.exceptions import DomainException, ConflictError


class InsufficientStockError(DomainException):
    """Raised when stock would go below zero."""
    http_status = 400


class DuplicateBarcodeError(ConflictError):
    """Raised when a barcode already exists."""


class DuplicateSKUError(ConflictError):
    """Raised when a SKU already exists."""
