"""Pydantic schemas for health and system information responses."""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ServiceComponentHealth(BaseModel):
    status: str
    configured: bool
    message: Optional[str] = None
    database: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status (healthy, degraded, unconfigured)")
    app_name: str
    version: str
    environment: str
    timestamp: str
    services: Dict[str, Any] = Field(default_factory=dict)


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    api_prefix: str
    services: Dict[str, Any]

