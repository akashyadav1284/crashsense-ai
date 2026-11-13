"""Pydantic schemas and models for screenshot-based Aviator analysis."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class AnalysisStatus(str, Enum):
    IDLE = "IDLE"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MultiplierRecord(BaseModel):
    sequence: int = Field(..., description="Monotonic 1-based order in sequence (1 = earliest or chronological)")
    multiplier: float = Field(..., ge=1.0, description="Extracted multiplier value (at least 1.00x)")
    ocr_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="OCR detection confidence")
    round_id: Optional[str] = Field(default=None, description="Extracted round ID if visible")
    timestamp: Optional[datetime] = Field(default=None, description="Extracted timestamp if visible")
    source: str = Field(default="SCREENSHOT_OCR", description="Always SCREENSHOT_OCR for screenshot extractions")
    verification_status: str = Field(default="UNVERIFIED", description="UNVERIFIED by default; USER_CONFIRMED after edit")
    is_flagged: bool = Field(default=False, description="Flagged for review or unreadable")
    raw_ocr_text: Optional[str] = Field(default=None, description="Original unparsed OCR token")


class MultiplierCorrectionUpdate(BaseModel):
    records: List[MultiplierRecord]


class MultiplierVerificationConfirm(BaseModel):
    save_to_historical_dataset: bool = Field(default=False, description="Whether to also register to historical dataset engine")
    dataset_name: Optional[str] = Field(default=None, description="Optional custom name if saving to datasets")


class StatisticalSummary(BaseModel):
    sample_size: int
    mean: float
    median: float
    std_dev: float
    min_multiplier: float
    max_multiplier: float
    frequencies: Dict[str, int]
    percentages: Dict[str, float]
    rolling_averages: List[float]
    autocorrelation_lag1: Optional[float] = None
    runs_test_p_value: Optional[float] = None
    independence_detected: Optional[bool] = None
    limitations: str = "Calculated exclusively over screenshot-extracted sample. Historical frequency does not imply future probability."


class CategoryProbability(BaseModel):
    category: str
    label: str
    historical_frequency_pct: float
    predicted_probability_pct: Optional[float] = None
    odds_estimate: Optional[float] = None


class NextRoundResearchEstimate(BaseModel):
    verdict: str = Field(
        default="NO_RELIABLE_PREDICTIVE_EDGE_DETECTED",
        description="Core verdict: NO_RELIABLE_PREDICTIVE_EDGE_DETECTED or VALIDATED_MODEL_ESTIMATE",
    )
    explanation: str
    model_status: str
    model_version: Optional[str] = None
    validation_status: str
    calibration_status: str
    categories: List[CategoryProbability]
    confidence_score: Optional[float] = None
    data_freshness_seconds: Optional[float] = None
    disclaimer: str = (
        "CrashSense AI provides experimental statistical analysis and research estimates. "
        "Previous Aviator multipliers do not guarantee or reliably determine future outcomes."
    )


class ScreenshotAnalysisResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    content_type: str
    file_size_bytes: int
    upload_timestamp: datetime
    extraction_status: ExtractionStatus
    analysis_status: AnalysisStatus
    platform: str = "spribe_aviator"
    game: str = "aviator"
    provider: str = "spribe"
    extracted_records: List[MultiplierRecord] = []
    user_confirmed_records: List[MultiplierRecord] = []
    data_quality_score: float = 0.0
    statistics: Optional[StatisticalSummary] = None
    research_estimate: Optional[NextRoundResearchEstimate] = None
    notes: Optional[str] = None
