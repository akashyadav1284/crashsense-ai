"""JSON Import Adapter."""
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.source import ConnectorCapabilities
from backend.app.connectors.schemas.connector import ConnectorHealthStatus
from backend.app.connectors.exceptions import RecordValidationError


class JSONImportAdapter(BaseConnector):
    """Parses and normalizes JSON arrays or NDJSON streams into Canonical Game Rounds."""

    def declare_capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_historical=True,
            supports_live_stream=False,
            supports_batch_export=True,
            supports_hash_verification=True
        )

    async def initialize(self) -> None:
        self.is_connected = True

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> None:
        self.is_connected = False

    async def health_check(self) -> ConnectorHealthStatus:
        return ConnectorHealthStatus(
            connector_id=self.connector_id,
            integration_type="JSON_IMPORT",
            connected=True,
            status="READY",
            latency_ms=0.0,
            last_verified=datetime.now(timezone.utc),
            message="JSON Parser adapter initialized and operational."
        )

    def normalize_record(self, raw_record: Dict[str, Any]) -> NormalizedGameRound:
        """Parse dictionary item from JSON into NormalizedGameRound."""
        round_id = raw_record.get("round_id") or raw_record.get("id")
        if not round_id:
            raise RecordValidationError("Missing round_id in JSON object")

        raw_mult = raw_record.get("multiplier") or raw_record.get("crash")
        try:
            multiplier = float(str(raw_mult).replace("x", "").replace("X", "").strip())
        except (ValueError, TypeError):
            raise RecordValidationError(f"Invalid multiplier: {raw_mult}")

        raw_ts = raw_record.get("round_timestamp") or raw_record.get("timestamp") or raw_record.get("time")
        round_ts = datetime.now(timezone.utc)
        if raw_ts:
            try:
                if isinstance(raw_ts, (int, float)):
                    round_ts = datetime.fromtimestamp(raw_ts / (1000 if raw_ts > 1e11 else 1), tz=timezone.utc)
                else:
                    round_ts = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
            except Exception:
                round_ts = datetime.now(timezone.utc)

        platform_id = raw_record.get("platform_id") or self.configuration.get("default_platform", "json_import")
        provider_id = raw_record.get("provider_id") or self.configuration.get("default_provider", "generic")
        game_id = raw_record.get("game_id") or self.configuration.get("default_game", "crash")
        room_id = raw_record.get("room_id") or self.configuration.get("default_room", "standard")
        hash_seed = raw_record.get("hash") or raw_record.get("seed") or ""

        return NormalizedGameRound(
            platform_id=str(platform_id).strip(),
            provider_id=str(provider_id).strip(),
            game_id=str(game_id).strip(),
            room_id=str(room_id).strip(),
            round_id=str(round_id).strip(),
            multiplier=multiplier,
            round_timestamp=round_ts,
            source_timestamp=round_ts,
            ingestion_timestamp=datetime.now(timezone.utc),
            source_type="JSON_IMPORT",
            source_record_id=str(round_id).strip(),
            verification_status="VERIFIED" if hash_seed else "UNVERIFIED",
            provenance={"raw": raw_record, "hash_seed": hash_seed}
        )

    def parse_json_content(self, json_text: str) -> List[Dict[str, Any]]:
        """Parses JSON text (array of records or lines)."""
        stripped = json_text.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            data = json.loads(stripped)
            if not isinstance(data, list):
                raise RecordValidationError("JSON payload must be a list of round objects")
            return data
        else:
            # Handle NDJSON
            records = []
            for line in stripped.splitlines():
                line = line.strip()
                if line:
                    records.append(json.loads(line))
            return records
