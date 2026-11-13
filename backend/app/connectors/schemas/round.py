"""Normalized Canonical Game Round Schema."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class NormalizedGameRound(BaseModel):
    """Canonical data model for crash multiplier round records across all sources."""
    platform_id: str = Field(..., description="Unique platform identifier (e.g. '1xbet', 'bcgame')")
    provider_id: str = Field(..., description="Game engine provider (e.g. 'spribe', 'inhouse')")
    game_id: str = Field(..., description="Game identifier (e.g. 'aviator', 'crash')")
    room_id: str = Field(..., description="Room / Table identifier (e.g. 'standard', 'highroller')")
    round_id: str = Field(..., description="Unique provider round number or hash ID")
    multiplier: float = Field(..., description="Final crash multiplier outcome (strictly finite positive number)")
    round_timestamp: datetime = Field(..., description="UTC timestamp of round crash event")
    source_timestamp: datetime = Field(..., description="UTC timestamp reported by data source")
    ingestion_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp when ingested")
    source_type: str = Field(..., description="Ingestion source type (e.g. 'OFFICIAL_REST', 'AUTHORIZED_WS', 'CSV_IMPORT', 'JSON_IMPORT')")
    source_record_id: str = Field(..., description="Original record ID from the raw ingest")
    verification_status: str = Field(default="UNVERIFIED", description="VERIFIED, UNVERIFIED, PENDING, or REJECTED")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Raw source metadata, headers, hash seeds, and payload")

    @field_validator("multiplier")
    @classmethod
    def validate_multiplier(cls, v: float) -> float:
        if v is None or v <= 0.0 or not (v == v):  # rejects NaN or negative
            raise ValueError("Multiplier must be a finite positive number greater than 0")
        return round(float(v), 4)

    @field_validator("round_id", "platform_id", "provider_id", "game_id", "room_id")
    @classmethod
    def validate_non_empty_strings(cls, v: str, info) -> str:
        if not v or not str(v).strip():
            raise ValueError(f"{info.field_name} must not be empty or whitespace")
        return str(v).strip()

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        valid_statuses = {"VERIFIED", "UNVERIFIED", "PENDING", "REJECTED"}
        v_upper = v.upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Verification status must be one of {valid_statuses}")
        return v_upper

    def compound_key(self) -> str:
        """Returns the canonical deduplication compound key."""
        return f"{self.platform_id}::{self.provider_id}::{self.game_id}::{self.room_id}::{self.round_id}"
