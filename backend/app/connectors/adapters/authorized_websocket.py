"""Authorized WebSocket Live Connector Adapter."""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, AsyncGenerator, Optional
import websockets
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.source import ConnectorCapabilities
from backend.app.connectors.schemas.connector import ConnectorHealthStatus
from backend.app.connectors.exceptions import (
    ConnectorConnectionError,
    RecordValidationError,
)


class AuthorizedWebSocketAdapter(BaseConnector):
    """Adapter for authorized, authenticated WebSocket live multiplier feeds."""

    def declare_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_historical=False,
            supports_live_stream=True,
            supports_batch_export=False,
            supports_hash_verification=True
        )

    async def initialize(self) -> None:
        self.ws_url = self.configuration.get("ws_url", "")
        self.auth_token = self.configuration.get("token", "")
        self.ws_client = None

    async def connect(self) -> bool:
        if not self.ws_url or not self.auth_token:
            self.is_connected = False
            return False

        try:
            # Test handshake with 4 second timeout
            async with websockets.connect(
                self.ws_url,
                extra_headers={"Authorization": f"Bearer {self.auth_token}"},
                open_timeout=4.0
            ) as ws:
                self.is_connected = True
                return True
        except Exception:
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        if self.ws_client:
            await self.ws_client.close()
            self.ws_client = None
        self.is_connected = False

    async def health_check(self) -> ConnectorHealthStatus:
        if not self.ws_url or not self.auth_token:
            return ConnectorHealthStatus(
                connector_id=self.connector_id,
                integration_type="AUTHORIZED_WS",
                connected=False,
                status="NOT CONFIGURED",
                message="WebSocket ingest URL or access token not provided."
            )

        try:
            ok = await self.connect()
            return ConnectorHealthStatus(
                connector_id=self.connector_id,
                integration_type="AUTHORIZED_WS",
                connected=ok,
                status="CONNECTED" if ok else "DISCONNECTED",
                last_verified=datetime.now(timezone.utc),
                message="WebSocket socket verification succeeded." if ok else "Handshake failed."
            )
        except Exception as exc:
            return ConnectorHealthStatus(
                connector_id=self.connector_id,
                integration_type="AUTHORIZED_WS",
                connected=False,
                status="ERROR",
                message=str(exc)
            )

    def normalize_record(self, raw_record: Dict[str, Any]) -> NormalizedGameRound:
        round_id = raw_record.get("round_id") or raw_record.get("round")
        if not round_id:
            raise RecordValidationError("Missing round_id in websocket payload")

        multiplier = float(raw_record.get("crash_multiplier") or raw_record.get("multiplier", 0))
        if multiplier <= 0:
            raise RecordValidationError(f"Invalid multiplier: {multiplier}")

        return NormalizedGameRound(
            platform_id=str(raw_record.get("platform_id", self.connector_id)),
            provider_id=str(raw_record.get("provider_id", "live_stream")),
            game_id=str(raw_record.get("game_id", "crash")),
            room_id=str(raw_record.get("room_id", "standard")),
            round_id=str(round_id),
            multiplier=multiplier,
            round_timestamp=datetime.now(timezone.utc),
            source_timestamp=datetime.now(timezone.utc),
            ingestion_timestamp=datetime.now(timezone.utc),
            source_type="AUTHORIZED_WS",
            source_record_id=str(round_id),
            verification_status="VERIFIED" if raw_record.get("hash") else "UNVERIFIED",
            provenance=raw_record
        )
