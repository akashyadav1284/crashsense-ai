"""Connector Exceptions."""


class ConnectorError(Exception):
    """Base exception for all connector-related failures."""
    pass


class UnsupportedCapabilityError(ConnectorError):
    """Raised when an operation is invoked that the connector does not support."""
    pass


class ConnectorAuthenticationError(ConnectorError):
    """Raised when authentication or authorization fails."""
    pass


class ConnectorConnectionError(ConnectorError):
    """Raised when a socket or HTTP connection fails."""
    pass


class RecordValidationError(ConnectorError):
    """Raised when an ingested record violates schema constraints."""
    pass


class DuplicateRecordError(ConnectorError):
    """Raised when a record has already been ingested into the canonical dataset."""
    pass
