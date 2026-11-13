"""Platform configuration schemas and models."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConnectorCapabilities(BaseModel):
    supports_historical: bool = False
    supports_live_stream: bool = False
    supports_batch_export: bool = False
    supports_hash_verification: bool = False


class PlatformConfig(BaseModel):
    platform_id: str = Field(..., description="Unique slug for the platform")
    platform_name: str = Field(..., description="Human-readable name")
    integration_type: str = Field(..., description="OFFICIAL_API, LICENSED_FEED, AUTHORIZED_WS, CSV_IMPORT, JSON_IMPORT")
    provider_name: str = Field(..., description="Default game provider for platform")
    authorization_status: str = Field(default="NOT CONFIGURED", description="AUTHORIZED, NOT CONFIGURED, AUTHORIZATION REQUIRED, INVALID_CREDENTIALS")
    connection_status: str = Field(default="DISCONNECTED", description="CONNECTED, DISCONNECTED, ERROR, STANDBY")
    capabilities: ConnectorCapabilities = Field(default_factory=ConnectorCapabilities)
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Endpoints, headers, and secrets (sanitized on export)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_successful_sync: Optional[datetime] = None
    last_error: Optional[str] = None


class PlatformCreateRequest(BaseModel):
    platform_id: str
    platform_name: str
    integration_type: str
    provider_name: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    capabilities: Optional[ConnectorCapabilities] = None


class PlatformUpdateRequest(BaseModel):
    platform_name: Optional[str] = None
    provider_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    authorization_status: Optional[str] = None
    connection_status: Optional[str] = None


class DataSourceResponse(BaseModel):
    source_id: str
    platform_id: str
    provider_id: str
    source_type: str
    status: str
    capabilities: ConnectorCapabilities
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
