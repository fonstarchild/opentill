from backend.shared.domain.exceptions import DomainException, ValidationError


class OrderAlreadyVoidedError(DomainException):
    """Raised when trying to void an already voided order."""
    http_status = 400


class EmptyOrderError(ValidationError):
    """Raised when trying to place an order with no items."""


class OrderNotCompletedError(DomainException):
    """Raised when an operation requires COMPLETED status."""
    http_status = 400
