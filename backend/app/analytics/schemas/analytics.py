"""Analytical Schemas and Response Contracts."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DescriptiveStatsResponse(BaseModel):
    dataset_id: str
    sample_size: int
    missing_count: int = 0
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    range: Optional[float] = None
    variance: Optional[float] = None
    std_dev: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    iqr: Optional[float] = None
    coefficient_of_variation: Optional[float] = None
    percentiles: Dict[str, float] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    warning: Optional[str] = None


class CategoryFrequencyItem(BaseModel):
    category: str
    range_min: float
    range_max: float
    count: int
    relative_frequency: float
    cumulative_count: int
    cumulative_relative_frequency: float
    confidence_interval: List[float] = Field(default_factory=list)


class DistributionResponse(BaseModel):
    dataset_id: str
    sample_size: int
    categories: List[CategoryFrequencyItem] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = (
        "Historical empirical frequencies describe past occurrences. "
        "They do not constitute predictive probabilities for independent future rounds."
    )


class RollingPoint(BaseModel):
    round_id: str
    timestamp: str
    rolling_mean: float
    rolling_median: float
    rolling_std: float
    rolling_min: float
    rolling_max: float
    observed_multiplier: float


class RollingStatsResponse(BaseModel):
    dataset_id: str
    window_size: int
    total_points: int
    series: List[RollingPoint] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notice: str = "Rolling metrics trace sample window moments only; they possess zero forward-predictive edge."


class IndependenceTestResult(BaseModel):
    test_name: str
    null_hypothesis: str
    alternative_hypothesis: str
    test_statistic: float
    p_value: float
    sample_size: int
    significance_threshold: float = 0.05
    reject_null: bool
    interpretation: str
    limitations: str


class AutocorrelationLag(BaseModel):
    lag: int
    autocorrelation: float
    confidence_bound: float
    statistically_significant: bool


class AutocorrelationResponse(BaseModel):
    dataset_id: str
    sample_size: int
    lags: List[AutocorrelationLag] = Field(default_factory=list)
    ljung_box: Optional[IndependenceTestResult] = None
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OutlierItem(BaseModel):
    round_id: str
    multiplier: float
    timestamp: str
    method: str
    reason: str
    category: str  # STATISTICAL_OUTLIER, DATA_QUALITY_ANOMALY


class OutlierResponse(BaseModel):
    dataset_id: str
    sample_size: int
    total_outliers: int
    outliers: List[OutlierItem] = Field(default_factory=list)
    iqr_bounds: Dict[str, float] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DriftComparisonResponse(BaseModel):
    dataset_id: str
    baseline_window: int
    comparison_window: int
    ks_test: IndependenceTestResult
    wasserstein_distance: float
    psi_score: float
    drift_status: str  # NO_DRIFT, MODERATE_DRIFT, SIGNIFICANT_DRIFT
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    warning: str = "Empirical drift measures distribution variance between windows and creates zero gambling edge."


class CrossPlatformComparisonResponse(BaseModel):
    platform_a: str
    platform_b: str
    sample_a: int
    sample_b: int
    mean_a: Optional[float] = None
    mean_b: Optional[float] = None
    median_a: Optional[float] = None
    median_b: Optional[float] = None
    ks_pvalue: Optional[float] = None
    divergence_score: float
    status: str
    disclaimer: str = "Different operators may employ distinct seed commitment protocols. Cross-platform pooling is prohibited."

