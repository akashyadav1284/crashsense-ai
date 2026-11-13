"""Data Models and Pydantic Schemas for Historical Datasets & Quality."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """Represents an isolated historical dataset slice for a specific platform/provider/room."""
    dataset_id: str = Field(..., description="Unique dataset identifier slug")
    platform_id: str
    provider_id: str
    game_id: str = "crash"
    room_id: str = "standard"
    dataset_name: str
    description: Optional[str] = None
    total_records: int = 0
    first_round_timestamp: Optional[datetime] = None
    last_round_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: str = "MIXED"  # CSV_IMPORT, JSON_IMPORT, OFFICIAL_REST, LICENSED_FEED
    data_quality_status: str = "UNASSESSED"  # EXCELLENT, ACCEPTABLE, DEGRADED, REJECTED, UNASSESSED
    quality_score: float = 0.0  # 0.0 to 100.0


class DatasetCreateRequest(BaseModel):
    dataset_id: str
    platform_id: str
    provider_id: str
    game_id: str = "crash"
    room_id: str = "standard"
    dataset_name: str
    description: Optional[str] = None


class ValidationRuleViolation(BaseModel):
    round_id: Optional[str]
    rule: str
    message: str
    severity: str  # ERROR, WARNING, CONFLICT


class DatasetValidationReport(BaseModel):
    report_id: str
    dataset_id: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_evaluated: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    conflict_records: int
    unverified_records: int
    timestamp_anomalies: int
    quality_score: float  # Computed 0.0 - 100.0
    status: str
    violations: List[ValidationRuleViolation] = Field(default_factory=list)


class DatasetCoverageReport(BaseModel):
    dataset_id: str
    total_records: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    timespan_hours: float = 0.0
    average_interval_seconds: float = 0.0
    gaps_detected: int = 0


class DatasetExportJob(BaseModel):
    export_id: str
    dataset_id: str
    format: str  # CSV, JSON
    total_records: int
    status: str  # PENDING, COMPLETED, FAILED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None


class PaginatedRoundsResponse(BaseModel):
    total_records: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    rounds: List[Dict[str, Any]]
