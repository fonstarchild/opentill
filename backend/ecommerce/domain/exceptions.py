from backend.shared.domain.exceptions import DomainException


class SyncError(DomainException):
    """Raised when a sync operation fails."""
    http_status = 502


class ConnectorAuthError(DomainException):
    """Raised when connector credentials are invalid."""
    http_status = 401


class ConnectorNotFoundError(DomainException):
    """Requested connector does not exist."""
    http_status = 404
