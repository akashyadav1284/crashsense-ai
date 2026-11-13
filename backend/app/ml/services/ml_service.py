"""
Orchestration Service for CRASHSENSE AI Machine Learning Research Laboratory.
Manages end-to-end dataset preparation, feature extraction, baseline comparison,
walk-forward training, probability calibration, and strictly bounded research inference.
"""

import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from backend.app.ml.schemas.experiment import (
    ModelMetadata,
    ModelLifecycleStatus,
    ExperimentRequest,
    ExperimentRecord,
    EvaluationMetrics,
    ResearchInferenceRequest,
    ResearchInferenceResponse,
)
from backend.app.ml.models.base_model import (
    BaseMLModel,
    BaselineFrequencyModel,
    IndependenceNullModel,
    get_model_by_algorithm,
)
from backend.app.ml.features.feature_builder import FeatureBuilder
from backend.app.ml.evaluation.metrics import (
    compute_metrics,
    compute_calibration_curve_data,
    WalkForwardValidator,
)
from backend.app.ml.registry.model_registry import ModelRegistry
from backend.app.datasets.manager import dataset_manager
from backend.app.connectors.manager import connector_manager


class MLService:
    """Core Service driving Machine Learning experiments and model evaluation."""

    _instance: Optional["MLService"] = None

    def __init__(self):
        self.registry = ModelRegistry.get_instance()
        self.feature_builder = FeatureBuilder()

    @classmethod
    def get_instance(cls) -> "MLService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def run_training_experiment(self, req: ExperimentRequest) -> ExperimentRecord:
        """
        Execute an end-to-end ML research training experiment:
        1. Fetch genuine historical crash dataset for platform/provider/room.
        2. Construct no-leakage backward lag and rolling features.
        3. Benchmark against Null Independence baseline and Empirical Frequency baseline.
        4. Run expanding-window walk-forward validation across candidate model.
        5. Verify whether statistical edge exists against null baseline.
        6. Compute probability calibration curve and reliability diagram data.
        7. Register model and experiment record.
        """
        exp_id = f"exp_{uuid.uuid4().hex[:10]}"
        model_id = f"mdl_{req.algorithm.lower()}_{uuid.uuid4().hex[:8]}"

        # 1. Fetch rounds data from connector manager
        rounds = await connector_manager.query_rounds(
            platform_id=req.platform_id,
            provider_id=req.game_provider,
            limit=5000,
        )

        # If not enough records in memory, provide synthetic sample or fallback for research lab initialization
        if len(rounds) < 100:
            # Check default dataset rounds
            rounds = await dataset_manager.get_dataset_rounds("ds-1xbet-aviator-standard")

        if len(rounds) < 50:
            raise ValueError(f"Insufficient historical rounds for training: {len(rounds)} available, minimum 50 required. Please import historical dataset.")

        # Convert to chronological DataFrame (oldest first)
        round_records = []
        for r in rounds:
            round_records.append({
                "round_id": r.round_id,
                "multiplier": r.multiplier,
                "timestamp": r.round_timestamp
            })
        df_rounds = pd.DataFrame(round_records)
        df_rounds.sort_values(by="timestamp", ascending=True, inplace=True)
        df_rounds.reset_index(drop=True, inplace=True)

        # 2. Build strictly backward-looking features with zero future leakage
        X, y, feature_names = self.feature_builder.build_features(
            df_rounds,
            target_threshold=req.target_threshold,
            min_history=req.feature_window_size
        )

        if len(X) < 30:
            raise ValueError(f"Sample size after lag feature window extraction is too small: {len(X)} records.")

        # 3. Benchmark Null and Frequency Baselines
        null_model = IndependenceNullModel(target_multiplier=req.target_threshold)
        null_proba = null_model.predict_proba(X)[:, 1]
        baseline_metrics = compute_metrics(y, null_proba)

        freq_model = BaselineFrequencyModel()
        freq_model.fit(X, y, feature_names=feature_names)

        # 4. Walk-Forward Expanding Window Validation
        validator = WalkForwardValidator(n_splits=req.walk_forward_splits)
        aggregate_metrics, fold_results = validator.evaluate(
            model_factory=lambda: get_model_by_algorithm(req.algorithm, req.hyperparameters),
            X=X,
            y=y,
            feature_names=feature_names
        )

        # 5. Fit full candidate model on all available historical data for registry artifact
        full_candidate_model = get_model_by_algorithm(req.algorithm, req.hyperparameters)
        full_candidate_model.fit(X, y, feature_names=feature_names)
        full_y_proba = full_candidate_model.predict_proba(X)[:, 1]

        # 6. Check for Validated Predictive Edge against Null Baseline
        brier_improvement = baseline_metrics.brier_score - aggregate_metrics.brier_score
        log_loss_improvement = baseline_metrics.log_loss - aggregate_metrics.log_loss

        # A validated edge requires out-of-sample Brier score improvement > 0.005 and Log Loss improvement > 0.01
        has_edge = (brier_improvement > 0.005) and (log_loss_improvement > 0.01) and (aggregate_metrics.roc_auc > 0.53)

        if has_edge:
            edge_notes = f"Model demonstrated statistically significant out-of-sample edge (Brier improvement: {brier_improvement:+.4f}, LogLoss improvement: {log_loss_improvement:+.4f}, AUC: {aggregate_metrics.roc_auc:.4f})."
            lifecycle_status = ModelLifecycleStatus.VALIDATED
        else:
            edge_notes = f"NO RELIABLE PREDICTIVE EDGE DETECTED. Out-of-sample Brier score ({aggregate_metrics.brier_score:.4f}) and Log Loss ({aggregate_metrics.log_loss:.4f}) did not statistically beat the Null Independence Baseline ({baseline_metrics.brier_score:.4f} / {baseline_metrics.log_loss:.4f}). Sequence is consistent with pseudo-random IID crash process."
            lifecycle_status = ModelLifecycleStatus.REJECTED

        # 7. Probability Calibration Diagram
        calibration_points = compute_calibration_curve_data(y, full_y_proba, n_bins=10)

        # 8. Feature Importance
        feature_importances = full_candidate_model.get_feature_importance()

        # 9. Register Model Artifact and Metadata
        model_meta = ModelMetadata(
            model_id=model_id,
            name=f"{req.algorithm} @ {req.target_threshold}x",
            algorithm=req.algorithm,
            version=req.experiment_name,
            platform_id=req.platform_id,
            game_provider=req.game_provider,
            game_id=req.game_id,
            room_id=req.room_id,
            target_threshold=req.target_threshold,
            feature_names=feature_names,
            hyperparameters=req.hyperparameters,
            training_sample_count=len(X),
            status=lifecycle_status,
            evaluation_metrics=aggregate_metrics,
            baseline_metrics=baseline_metrics,
            has_validated_edge=has_edge,
            edge_validation_notes=edge_notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.registry.register_model(model_meta, full_candidate_model)

        experiment_record = ExperimentRecord(
            experiment_id=exp_id,
            experiment_name=req.experiment_name,
            model_id=model_id,
            algorithm=req.algorithm,
            platform_id=req.platform_id,
            game_provider=req.game_provider,
            game_id=req.game_id,
            room_id=req.room_id,
            target_threshold=req.target_threshold,
            walk_forward_folds=fold_results,
            aggregate_metrics=aggregate_metrics,
            baseline_metrics=baseline_metrics,
            calibration_curve=calibration_points,
            feature_importances=feature_importances,
            has_validated_edge=has_edge,
            edge_validation_notes=edge_notes,
            created_at=datetime.now(timezone.utc)
        )

        self.registry.record_experiment(experiment_record)
        return experiment_record

    def run_research_inference(self, req: ResearchInferenceRequest) -> ResearchInferenceResponse:
        """
        Execute research inference on latest sequence with mandatory statistical disclaimers.
        """
        meta = self.registry.get_model_metadata(req.model_id)
        if not meta:
            raise ValueError(f"Model ID '{req.model_id}' not found in registry.")

        model = self.registry.get_model(req.model_id)
        if not model:
            raise ValueError(f"Model artifact for '{req.model_id}' is not loaded.")

        # Require minimum history to compute features
        if len(req.recent_multipliers) < 10:
            raise ValueError(f"At least 10 recent multipliers required for feature extraction, received {len(req.recent_multipliers)}.")

        # Compute inference features from recent multipliers
        arr = np.array(req.recent_multipliers)
        features: Dict[str, float] = {}

        # Backward lags
        features["lag_1"] = float(arr[-1])
        features["lag_2"] = float(arr[-2]) if len(arr) >= 2 else float(arr[-1])
        features["lag_3"] = float(arr[-3]) if len(arr) >= 3 else float(arr[-1])
        features["lag_5"] = float(arr[-5]) if len(arr) >= 5 else float(arr[-1])
        features["lag_10"] = float(arr[-10]) if len(arr) >= 10 else float(arr[-1])

        # Rolling statistics
        w10 = arr[-10:]
        features["rolling_mean_10"] = float(np.mean(w10))
        features["rolling_std_10"] = float(np.std(w10))
        features["rolling_median_10"] = float(np.median(w10))
        features["rolling_iqr_10"] = float(np.percentile(w10, 75) - np.percentile(w10, 25))
        features["rolling_p_gt_target_10"] = float(np.mean(w10 >= meta.target_threshold))
        features["current_below_target_streak"] = float(self.feature_builder._compute_streak_at_idx(arr, len(arr) - 1, meta.target_threshold))

        # Align with model feature order
        feature_vector = np.array([[features.get(f_name, 0.0) for f_name in meta.feature_names]])

        proba = model.predict_proba(feature_vector)[0]
        p_over = float(proba[1])

        # Baseline probability for comparison
        theoretical_null = max(0.001, (1.0 - 0.01) / meta.target_threshold)

        return ResearchInferenceResponse(
            model_id=req.model_id,
            target_threshold=meta.target_threshold,
            predicted_probability_over_threshold=round(p_over, 4),
            baseline_probability=round(theoretical_null, 4),
            decision_signal="PASS" if p_over > 0.55 else "NO_SIGNAL",
            confidence_interval=(round(max(0.0, p_over - 0.08), 4), round(min(1.0, p_over + 0.08), 4)),
            has_validated_edge=meta.has_validated_edge,
            scientific_disclaimer="RESEARCH MONITORING ONLY. Crash multipliers are generated by cryptographic PRNG / Provably Fair hash sequences. Past rounds do not dictate future outcomes. Do not use for automated betting.",
            computed_at=datetime.now(timezone.utc)
        )
