# CRASHSENSE AI - Data Connector Guide

## 1. Overview
The CrashSense AI data connector engine provides a modular abstraction for streaming and batch-ingesting crash game multipliers from external data sources.

### Core Connector Architecture
All connectors implement `backend.app.connectors.base.BaseConnector`:
- `initialize()`: Sets up clients, tokens, and endpoint routes.
- `connect()`: Tests authentication or initiates WebSocket handshake.
- `disconnect()`: Closes resources gracefully.
- `health_check()`: Returns `ConnectorHealthStatus` (latency, connected flag, message).
- `fetch_historical()`: Paginated historical ingest.
- `subscribe_live()`: Asynchronous WebSocket stream.
- `normalize_record()`: Maps provider-specific payloads to `NormalizedGameRound`.

---

## 2. Supported Ingestion Adapters

| Adapter | Class | Integration Type | Description |
| :--- | :--- | :--- | :--- |
| **Official REST API** | `OfficialAPIAdapter` | `OFFICIAL_API`, `OFFICIAL_REST` | Authorized HTTP endpoints with Bearer/API-Key tokens. |
| **Licensed Feed** | `OfficialAPIAdapter` | `LICENSED_FEED` | Commercial aggregator feeds. |
| **Authorized WebSocket**| `AuthorizedWebSocketAdapter` | `AUTHORIZED_WS` | Real-time socket ingest with heartbeat and backoff. |
| **CSV File Import** | `CSVImportAdapter` | `CSV_IMPORT` | Parses user-provided historical multiplier CSV files. |
| **JSON File Import**| `JSONImportAdapter` | `JSON_IMPORT` | Parses user-provided historical JSON / NDJSON arrays. |

---

## 3. How to Register a New Authorized Connector

1. Create a new adapter file in `backend/app/connectors/adapters/your_platform.py`.
2. Inherit from `BaseConnector` and implement required abstract methods:
   ```python
   from backend.app.connectors.base import BaseConnector
   from backend.app.connectors.schemas import NormalizedGameRound, ConnectorCapabilities

   class CustomPlatformAdapter(BaseConnector):
       def declare_capabilities(self) -> ConnectorCapabilities:
           return ConnectorCapabilities(supports_historical=True, supports_live_stream=True)

       async def initialize(self): ...
       async def connect(self) -> bool: ...
       async def disconnect(self): ...
       async def health_check(self): ...
       def normalize_record(self, raw_record) -> NormalizedGameRound: ...
   ```
3. Register the adapter in `backend/app/connectors/registry.py`:
   ```python
   connector_registry.register_adapter("CUSTOM_PLATFORM", CustomPlatformAdapter)
   ```
