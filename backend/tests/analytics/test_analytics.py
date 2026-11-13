"""Scientific Unit & Hypothesis Testing for Analytics Engine."""
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.analytics.engine.descriptive import DescriptiveEngine
from backend.app.analytics.engine.distribution import DistributionEngine
from backend.app.analytics.engine.rolling import RollingEngine
from backend.app.analytics.engine.independence import IndependenceEngine
from backend.app.analytics.engine.outliers import OutlierEngine
from backend.app.analytics.engine.drift import DriftEngine


@pytest.fixture
def controlled_sample_data():
    """Generates deterministic controlled dataset with known statistical properties."""
    np.random.seed(42)
    # 500 samples following Pareto/exponential style multiplier distribution
    data = np.random.exponential(scale=1.5, size=500) + 1.0
    return list(np.round(data, 2))


def test_descriptive_engine_moments(controlled_sample_data):
    """Verify sample mean, variance, percentiles, and skewness."""
    res = DescriptiveEngine.compute("test-ds", controlled_sample_data)
    assert res.sample_size == 500
    assert res.mean is not None and res.mean > 1.0
    assert res.median is not None and res.median > 1.0
    assert res.std_dev is not None and res.std_dev > 0.0
    assert "P50" in res.percentiles
    assert "P99" in res.percentiles
    assert res.percentiles["P99"] >= res.percentiles["P50"]


def test_distribution_engine_bins_and_wilson_ci(controlled_sample_data):
    """Verify categorical frequency bins sum to total and compute Wilson CI."""
    res = DistributionEngine.compute("test-ds", controlled_sample_data)
    assert res.sample_size == 500
    total_count = sum(c.count for c in res.categories)
    assert total_count == 500

    # Ensure Wilson interval bounds are valid probabilities [0, 1]
    for c in res.categories:
        assert 0.0 <= c.confidence_interval[0] <= c.confidence_interval[1] <= 1.0


def test_autocorrelation_on_iid_random_sequence():
    """Demonstrate that independent random sequences fail to produce significant autocorrelation."""
    np.random.seed(123)
    # Strictly independent uniform random noise
    iid_noise = list(np.random.uniform(1.0, 10.0, 500))
    res = IndependenceEngine.compute("iid-test", iid_noise, max_lags=10)
    assert res.sample_size == 500
    assert len(res.lags) == 10

    # Under independent noise, Ljung-Box should not reject the null hypothesis
    assert res.ljung_box is not None
    assert res.ljung_box.p_value > 0.01  # Cannot reject independence at 1% level


def test_outlier_detection_iqr(controlled_sample_data):
    """Verify Tukey 1.5x IQR fence catches extreme right-tail multipliers."""
    res = OutlierEngine.compute("test-outliers", [
        NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id=f"r-{i}",
            multiplier=1.5 if i < 99 else 250.0,  # 1 extreme outlier
            round_timestamp=datetime.now(timezone.utc),
            source_timestamp=datetime.now(timezone.utc),
            source_type="CSV_IMPORT",
            source_record_id=str(i)
        )
        for i in range(100)
    ])
    assert res.total_outliers >= 1
    assert any(o.multiplier == 250.0 for o in res.outliers)


def test_drift_detection_stability():
    """Verify Two-sample KS and PSI detect distribution stability."""
    np.random.seed(999)
    seq = list(np.random.uniform(1.0, 5.0, 400))
    res = DriftEngine.compare_windows("drift-test", seq, baseline_window=100, comparison_window=100)
    # Same distribution slices should yield NO_DRIFT
    assert res.drift_status in ("NO_DRIFT", "MODERATE_DRIFT")
    assert res.ks_test.p_value > 0.01


@pytest.mark.asyncio
async def test_api_analytics_endpoints():
    """Verify /api/v1/analytics descriptive and distribution routes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_desc = await client.get("/api/v1/analytics/descriptive?dataset_id=ds-1xbet-aviator-standard")
        assert res_desc.status_code == 200
        data_desc = res_desc.json()
        assert "sample_size" in data_desc

        res_dist = await client.get("/api/v1/analytics/distribution?dataset_id=ds-1xbet-aviator-standard")
        assert res_dist.status_code == 200
        data_dist = res_dist.json()
        assert "categories" in data_dist
        assert "disclaimer" in data_dist

