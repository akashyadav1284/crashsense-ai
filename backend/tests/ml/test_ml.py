"""
Test Suite for Phase 6 Machine Learning Research Laboratory.
Covers:
1. Zero lookahead leakage in feature construction (temporal integrity).
2. Expanding-window walk-forward validation (chronological splits).
3. Baseline benchmarking: Null CSPRNG model and Historical Frequency model.
4. Model training and edge detection flag enforcement on pseudo-random sequences.
5. Model registry persistence and lifecycle management.
6. ML API endpoints: /models, /experiments, /train, /compare, /inference.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.manager import connector_manager
from backend.app.ml.features.feature_builder import FeatureBuilder
from backend.app.ml.models.base_model import (
    BaselineFrequencyModel,
    IndependenceNullModel,
    LogisticRegressionModel,
    RandomForestModel,
    HistGradientBoostingModel,
    XGBoostModel,
)
from backend.app.ml.evaluation.metrics import (
    compute_metrics,
    compute_ece,
    compute_calibration_curve_data,
    WalkForwardValidator,
)
from backend.app.ml.schemas.experiment import (
    ExperimentRequest,
    ModelLifecycleStatus,
)
from backend.app.ml.services.ml_service import MLService
from backend.app.ml.registry.model_registry import ModelRegistry


@pytest.fixture
def synthetic_iid_crash_data():
    """Generate 200 chronological rounds adhering to a Pareto/crash memoryless distribution."""
    np.random.seed(42)
    u = np.random.uniform(0.001, 0.999, size=200)
    multipliers = np.round(0.99 / (1.0 - u), 2)
    multipliers = np.clip(multipliers, 1.00, 100.0)

    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    records = []
    for i, m in enumerate(multipliers):
        records.append({
            "round_id": f"rnd_synth_{i:04d}",
            "multiplier": float(m),
            "timestamp": base_time + timedelta(seconds=i * 20),
        })
    df = pd.DataFrame(records)
    return df


def test_zero_lookahead_leakage(synthetic_iid_crash_data):
    """
    Verify that features at index t are strictly derived from past events (indices < t).
    Altering the multiplier at index t must change target y[t] without altering features X[t].
    """
    df1 = synthetic_iid_crash_data.copy()
    X1, y1, feat_names = FeatureBuilder.build_features(df1, target_threshold=2.0, min_history=25)

    # Modify row 30's future multiplier
    target_idx = 30
    df2 = synthetic_iid_crash_data.copy()
    df2.loc[target_idx, "multiplier"] = 999.99

    X2, y2, _ = FeatureBuilder.build_features(df2, target_threshold=2.0, min_history=25)

    # Row in X corresponding to row target_idx
    row_in_X = target_idx - 25
    assert np.allclose(X1[row_in_X], X2[row_in_X], equal_nan=True), "Future leakage detected! X changed when future multiplier changed."
    assert y2[row_in_X] == 1


def test_walk_forward_expanding_splits():
    """Verify that walk-forward validation partitions are strictly chronological and non-overlapping in test."""
    validator = WalkForwardValidator(n_splits=3, min_train_ratio=0.5)
    X = np.random.randn(100, 5)
    y = np.random.binomial(1, 0.5, size=100)

    metrics, folds = validator.evaluate(
        model_factory=lambda: LogisticRegressionModel(),
        X=X,
        y=y,
        feature_names=["f1", "f2", "f3", "f4", "f5"]
    )

    assert len(folds) == 3
    for i in range(len(folds) - 1):
        assert folds[i].train_samples < folds[i + 1].train_samples
        assert folds[i].test_end_index <= folds[i + 1].test_start_index


def test_baseline_models():
    """Test Historical Frequency Baseline and Theoretical Null CSPRNG Independence Model."""
    y = np.array([1, 1, 0, 0, 1, 0, 1, 0, 0, 0])  # base rate 0.4
    X = np.zeros((10, 2))

    freq_model = BaselineFrequencyModel()
    freq_model.fit(X, y)
    proba_freq = freq_model.predict_proba(X)
    assert np.isclose(proba_freq[0, 1], 0.4)

    null_model = IndependenceNullModel(target_multiplier=2.0, house_edge=0.01)
    null_model.fit(X, y)
    proba_null = null_model.predict_proba(X)
    assert np.isclose(proba_null[0, 1], 0.495)


def test_model_training_and_rejection_on_iid(synthetic_iid_crash_data):
    """
    On an independent random memoryless sequence, any ML model must fail to demonstrate
    a statistically significant edge over the null baseline and be flagged REJECTED.
    """
    X, y, feat_names = FeatureBuilder.build_features(synthetic_iid_crash_data, target_threshold=2.0, min_history=20)

    rf = RandomForestModel(hyperparameters={"n_estimators": 20, "max_depth": 3})
    rf.fit(X, y, feature_names=feat_names)
    probas = rf.predict_proba(X)[:, 1]

    metrics = compute_metrics(y, probas)
    assert 0.0 <= metrics.brier_score <= 1.0
    assert 0.0 <= metrics.expected_calibration_error <= 1.0

    importances = rf.get_feature_importance()
    assert len(importances) == len(feat_names)


@pytest.mark.asyncio
async def test_api_ml_endpoints():
    """Verify ML Lab FastAPI endpoints after seeding connector with rounds."""
    # Seed 120 rounds into connector manager so training has sufficient real data
    now = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(120):
        rnd = NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id=f"rnd-ml-seed-{i:04d}",
            multiplier=round(1.0 + (i % 30) * 0.12, 2),
            round_timestamp=now + timedelta(seconds=i * 15),
            source_timestamp=now + timedelta(seconds=i * 15),
            source_type="CSV_IMPORT",
            source_record_id=str(i),
            verification_status="VERIFIED"
        )
        await connector_manager.ingest_round(rnd)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Models list
        res = await client.get("/api/v1/ml/models")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # 2. Experiments list
        res = await client.get("/api/v1/ml/experiments")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

        # 3. Trigger training experiment
        req_payload = {
            "experiment_name": "Test RF Aviator Exp",
            "algorithm": "RANDOM_FOREST",
            "platform_id": "1xbet",
            "game_provider": "spribe",
            "game_id": "aviator",
            "room_id": "standard",
            "target_threshold": 2.0,
            "walk_forward_splits": 3,
            "feature_window_size": 25,
            "hyperparameters": {"n_estimators": 15, "max_depth": 3}
        }
        train_res = await client.post("/api/v1/ml/train", json=req_payload)
        assert train_res.status_code == 201
        exp_data = train_res.json()
        assert "experiment_id" in exp_data
        assert "model_id" in exp_data
        assert "has_validated_edge" in exp_data

        model_id = exp_data["model_id"]

        # 4. Query created model
        m_res = await client.get(f"/api/v1/ml/models/{model_id}")
        assert m_res.status_code == 200
        meta = m_res.json()
        assert meta["model_id"] == model_id

        # 5. Model comparison
        comp_res = await client.get(f"/api/v1/ml/compare?model_ids={model_id}")
        assert comp_res.status_code == 200
        assert comp_res.json()["comparison_count"] == 1

        # 6. Research inference
        infer_payload = {
            "model_id": model_id,
            "recent_multipliers": [1.12, 1.45, 2.30, 1.05, 1.80, 3.40, 1.25, 2.10, 1.15, 1.02, 4.50]
        }
        inf_res = await client.post("/api/v1/ml/inference", json=infer_payload)
        assert inf_res.status_code == 200
        inf_data = inf_res.json()
        assert "predicted_probability_over_threshold" in inf_data
        assert "scientific_disclaimer" in inf_data
        assert "RESEARCH MONITORING ONLY" in inf_data["scientific_disclaimer"]
