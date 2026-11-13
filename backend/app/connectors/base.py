"""Base Abstract Connector Class."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.source import ConnectorCapabilities
from backend.app.connectors.schemas.connector import ConnectorHealthStatus
from backend.app.connectors.exceptions import UnsupportedCapabilityError


class BaseConnector(ABC):
    """Abstract interface that all data connectors must implement."""

    def __init__(self, connector_id: str, configuration: Dict[str, Any]):
        self.connector_id = connector_id
        self.configuration = configuration
        self.capabilities = self.declare_capabilities()
        self.is_connected = False

    @abstractmethod
    def declare_capabilities(self) -> ConnectorCapabilities:
        """Explicitly declare what this adapter supports."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Prepare credentials, configure HTTP clients, or validate input parameters."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to live source or verify API authentication."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully terminate connection resources."""
        pass

    @abstractmethod
    async def health_check(self) -> ConnectorHealthStatus:
        """Report live connection health, status, and latency."""
        pass

    async def fetch_historical(
        self,
        limit: int = 1000,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        **kwargs
    ) -> List[NormalizedGameRound]:
        """Fetch historical records. Raises error if unsupported."""
        if not self.capabilities.supports_historical:
            raise UnsupportedCapabilityError(
                f"Connector '{self.connector_id}' does not support historical data fetching."
            )
        return []

    async def subscribe_live(self) -> AsyncGenerator[NormalizedGameRound, None]:
        """Stream real-time rounds as an async generator."""
        if not self.capabilities.supports_live_stream:
            raise UnsupportedCapabilityError(
                f"Connector '{self.connector_id}' does not support live streaming."
            )
        # Yield nothing by default for base
        if False:
            yield

    @abstractmethod
    def normalize_record(self, raw_record: Dict[str, Any]) -> NormalizedGameRound:
        """Map heterogeneous source fields to the canonical NormalizedGameRound."""
        pass

    def validate_record(self, record: NormalizedGameRound) -> bool:
        """Verify business validation logic beyond basic Pydantic constraints."""
        if record.multiplier <= 0:
            return False
        if not record.round_id or not record.platform_id:
            return False
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Return connector capabilities and current configuration (sanitized)."""
        return {
            "connector_id": self.connector_id,
            "connected": self.is_connected,
            "capabilities": self.capabilities.model_dump(),
            "configuration": {
                k: ("***" if "secret" in k.lower() or "key" in k.lower() or "token" in k.lower() else v)
                for k, v in self.configuration.items()
            }
        }
