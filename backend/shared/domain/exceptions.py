class DomainException(Exception):
    """Base class for domain exceptions."""
    http_status: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainException):
    """Raised when a requested entity is not found."""
    http_status = 404


class ValidationError(DomainException):
    """Raised when domain validation fails."""
    http_status = 422


class ConflictError(DomainException):
    """Raised when a conflict occurs (e.g. duplicate)."""
    http_status = 409
