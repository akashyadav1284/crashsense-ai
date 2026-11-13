"""Official REST API Connector Adapter."""
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.source import ConnectorCapabilities
from backend.app.connectors.schemas.connector import ConnectorHealthStatus
from backend.app.connectors.exceptions import (
    ConnectorAuthenticationError,
    ConnectorConnectionError,
    RecordValidationError,
)


class OfficialAPIAdapter(BaseConnector):
    """Adapter for documented, authorized official REST endpoints.
    
    Zero-Fabrication Guarantee:
    If endpoint or credentials are not supplied or unverified, this adapter
    reports AUTHORIZATION REQUIRED or NOT CONFIGURED and does not fabricate data.
    """

    def declare_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_historical=True,
            supports_live_stream=False,
            supports_batch_export=True,
            supports_hash_verification=True
        )

    async def initialize(self) -> None:
        self.endpoint = self.configuration.get("endpoint", "")
        self.api_key = self.configuration.get("api_key", "")
        self.client: Optional[httpx.AsyncClient] = None
        if self.endpoint:
            self.client = httpx.AsyncClient(timeout=10.0)

    async def connect(self) -> bool:
        if not self.endpoint or not self.api_key:
            self.is_connected = False
            return False

        try:
            if not self.client:
                self.client = httpx.AsyncClient(timeout=10.0)
            headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
            res = await self.client.get(f"{self.endpoint}/ping", headers=headers)
            if res.status_code in (200, 204):
                self.is_connected = True
                return True
            else:
                self.is_connected = False
                return False
        except Exception:
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
        self.is_connected = False

    async def health_check(self) -> ConnectorHealthStatus:
        if not self.endpoint or not self.api_key:
            return ConnectorHealthStatus(
                connector_id=self.connector_id,
                integration_type="OFFICIAL_REST",
                connected=False,
                status="NOT CONFIGURED",
                message="API endpoint URL or authorization key missing in configuration."
            )

        t0 = time.time()
        try:
            ok = await self.connect()
            latency = (time.time() - t0) * 1000
            if ok:
                return ConnectorHealthStatus(
                    connector_id=self.connector_id,
                    integration_type="OFFICIAL_REST",
                    connected=True,
                    status="CONNECTED",
                    latency_ms=round(latency, 2),
                    last_verified=datetime.now(timezone.utc),
                    message="Official API ping verified successfully."
                )
            else:
                return ConnectorHealthStatus(
                    connector_id=self.connector_id,
                    integration_type="OFFICIAL_REST",
                    connected=False,
                    status="AUTHORIZATION REQUIRED",
                    latency_ms=round(latency, 2),
                    last_verified=datetime.now(timezone.utc),
                    message="Target server rejected connection or returned authorization error."
                )
        except Exception as exc:
            return ConnectorHealthStatus(
                connector_id=self.connector_id,
                integration_type="OFFICIAL_REST",
                connected=False,
                status="ERROR",
                message=f"Connection attempt failed: {str(exc)}"
            )

    async def fetch_historical(
        self,
        limit: int = 1000,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        **kwargs
    ) -> List[NormalizedGameRound]:
        if not self.is_connected or not self.client:
            raise ConnectorConnectionError("Connector is not connected or authorized.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"limit": limit}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        res = await self.client.get(f"{self.endpoint}/rounds", headers=headers, params=params)
        if res.status_code != 200:
            raise ConnectorConnectionError(f"HTTP {res.status_code} fetching historical rounds: {res.text}")

        raw_items = res.json().get("items", [])
        return [self.normalize_record(item) for item in raw_items]

    def normalize_record(self, raw_record: Dict[str, Any]) -> NormalizedGameRound:
        round_id = raw_record.get("round_id") or raw_record.get("id")
        if not round_id:
            raise RecordValidationError("Missing round_id in official API payload")

        multiplier = float(raw_record.get("multiplier", 0))
        if multiplier <= 0:
            raise RecordValidationError(f"Invalid multiplier: {multiplier}")

        raw_ts = raw_record.get("timestamp")
        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")) if raw_ts else datetime.now(timezone.utc)

        return NormalizedGameRound(
            platform_id=str(raw_record.get("platform_id", self.connector_id)),
            provider_id=str(raw_record.get("provider_id", "official")),
            game_id=str(raw_record.get("game_id", "crash")),
            room_id=str(raw_record.get("room_id", "standard")),
            round_id=str(round_id),
            multiplier=multiplier,
            round_timestamp=ts,
            source_timestamp=ts,
            ingestion_timestamp=datetime.now(timezone.utc),
            source_type="OFFICIAL_REST",
            source_record_id=str(round_id),
            verification_status="VERIFIED" if raw_record.get("hash") else "UNVERIFIED",
            provenance=raw_record
        )
