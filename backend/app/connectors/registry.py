"""Connector Registry."""
from typing import Dict, Type
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.adapters.csv_import import CSVImportAdapter
from backend.app.connectors.adapters.json_import import JSONImportAdapter
from backend.app.connectors.adapters.official_api import OfficialAPIAdapter
from backend.app.connectors.adapters.authorized_websocket import AuthorizedWebSocketAdapter


class ConnectorRegistry:
    """Registry mapping integration types to concrete adapter classes."""

    _adapters: Dict[str, Type[BaseConnector]] = {
        "CSV_IMPORT": CSVImportAdapter,
        "JSON_IMPORT": JSONImportAdapter,
        "OFFICIAL_API": OfficialAPIAdapter,
        "OFFICIAL_REST": OfficialAPIAdapter,
        "LICENSED_FEED": OfficialAPIAdapter,
        "AUTHORIZED_WS": AuthorizedWebSocketAdapter,
        "WEBSOCKET": AuthorizedWebSocketAdapter,
    }

    @classmethod
    def register_adapter(cls, integration_type: str, adapter_cls: Type[BaseConnector]) -> None:
        cls._adapters[integration_type.upper()] = adapter_cls

    @classmethod
    def get_adapter_class(cls, integration_type: str) -> Type[BaseConnector]:
        norm = integration_type.upper().replace(" ", "_")
        adapter_cls = cls._adapters.get(norm)
        if not adapter_cls:
            raise ValueError(f"Unknown integration type: {integration_type}. Supported: {list(cls._adapters.keys())}")
        return adapter_cls

    @classmethod
    def list_supported_types(cls) -> Dict[str, str]:
        return {
            "OFFICIAL_API": "Documented REST API with OAuth2/Bearer Token",
            "LICENSED_FEED": "Authorized Commercial Data Feed Provider",
            "AUTHORIZED_WS": "Real-Time WebSocket Protocol with Token Handshake",
            "CSV_IMPORT": "User-Provided Historical CSV Multiplier File",
            "JSON_IMPORT": "User-Provided Historical JSON / NDJSON File",
        }


connector_registry = ConnectorRegistry
