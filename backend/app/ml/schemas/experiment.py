"""ML Data Contracts and Experiment Schemas."""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class ModelLifecycleStatus(str, Enum):
    CREATED = "CREATED"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    EVALUATED = "EVALUATED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class EvaluationMetrics(BaseModel):
    accuracy: float = 0.0
    balanced_accuracy: float = 0.0
    brier_score: float = 0.25
    log_loss: float = 0.69315
    roc_auc: float = 0.5
    expected_calibration_error: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    confusion_matrix: List[List[int]] = Field(default_factory=lambda: [[0, 0], [0, 0]])


class WalkForwardFoldResult(BaseModel):
    fold_index: int
    train_start_index: int
    train_end_index: int
    test_start_index: int
    test_end_index: int
    train_samples: int
    test_samples: int
    metrics: EvaluationMetrics


class ModelMetadata(BaseModel):
    model_id: str
    name: str
    algorithm: str  # LOGISTIC_REGRESSION, RANDOM_FOREST, HIST_GRADIENT_BOOSTING, XGBOOST, BASELINE_FREQUENCY, NULL_INDEPENDENCE
    version: str = "v1.0.0"
    platform_id: str
    game_provider: str
    game_id: str
    room_id: str
    target_threshold: float = 2.0
    feature_names: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    training_sample_count: int = 0
    status: ModelLifecycleStatus = ModelLifecycleStatus.CREATED
    evaluation_metrics: EvaluationMetrics = Field(default_factory=EvaluationMetrics)
    baseline_metrics: Optional[EvaluationMetrics] = None
    has_validated_edge: bool = False
    edge_validation_notes: str = ""
    model_file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExperimentRequest(BaseModel):
    experiment_name: str
    algorithm: str = "RANDOM_FOREST"  # LOGISTIC_REGRESSION, RANDOM_FOREST, HIST_GRADIENT_BOOSTING, XGBOOST
    platform_id: str = "1xbet"
    game_provider: str = "spribe"
    game_id: str = "aviator"
    room_id: str = "standard"
    target_threshold: float = 2.0
    walk_forward_splits: int = 4
    feature_window_size: int = 50
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)


class ExperimentRecord(BaseModel):
    experiment_id: str
    experiment_name: str
    model_id: str
    algorithm: str
    platform_id: str
    game_provider: str
    game_id: str
    room_id: str
    target_threshold: float
    walk_forward_folds: List[WalkForwardFoldResult] = Field(default_factory=list)
    aggregate_metrics: EvaluationMetrics = Field(default_factory=EvaluationMetrics)
    baseline_metrics: Optional[EvaluationMetrics] = None
    calibration_curve: List[Dict[str, Any]] = Field(default_factory=list)
    feature_importances: Dict[str, float] = Field(default_factory=dict)
    has_validated_edge: bool = False
    edge_validation_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchInferenceRequest(BaseModel):
    model_id: str
    recent_multipliers: List[float] = Field(..., min_length=10, description="Chronological sequence of recent multiplier outcomes, oldest to newest")


class ResearchInferenceResponse(BaseModel):
    model_id: str
    target_threshold: float
    predicted_probability_over_threshold: float
    baseline_probability: float
    decision_signal: str  # "PASS", "NO_SIGNAL"
    confidence_interval: Tuple[float, float]
    has_validated_edge: bool
    scientific_disclaimer: str
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
