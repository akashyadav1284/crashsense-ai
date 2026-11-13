"""Connector schemas and Import Job Models."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ImportJob(BaseModel):
    job_id: str
    source_id: str
    source_type: str
    total_records: int = 0
    processed_records: int = 0
    accepted_records: int = 0
    rejected_records: int = 0
    duplicate_records: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = Field(default="PENDING", description="PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED")
    errors: List[str] = Field(default_factory=list)


class DataQualityEvent(BaseModel):
    event_id: str
    round_id: Optional[str] = None
    source_id: str
    severity: str = Field(..., description="INFO, WARNING, ERROR, CRITICAL")
    reason: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectorHealthStatus(BaseModel):
    connector_id: str
    integration_type: str
    connected: bool
    status: str
    latency_ms: Optional[float] = None
    last_verified: Optional[datetime] = None
    message: str
