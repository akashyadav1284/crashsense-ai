"""Statistical Analytics Service."""
from typing import List, Dict, Any, Optional
from scipy import stats
import numpy as np
from backend.app.datasets.manager import dataset_manager
from backend.app.analytics.engine.descriptive import DescriptiveEngine
from backend.app.analytics.engine.distribution import DistributionEngine
from backend.app.analytics.engine.rolling import RollingEngine
from backend.app.analytics.engine.independence import IndependenceEngine
from backend.app.analytics.engine.outliers import OutlierEngine
from backend.app.analytics.engine.drift import DriftEngine
from backend.app.analytics.schemas.analytics import (
    DescriptiveStatsResponse,
    DistributionResponse,
    RollingStatsResponse,
    AutocorrelationResponse,
    OutlierResponse,
    DriftComparisonResponse,
    CrossPlatformComparisonResponse,
)


class AnalyticsService:
    """Orchestrates statistical engines over dataset partitions."""

    @classmethod
    async def get_descriptive_stats(cls, dataset_id: str) -> DescriptiveStatsResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        multipliers = [r.multiplier for r in rounds]
        return DescriptiveEngine.compute(dataset_id, multipliers)

    @classmethod
    async def get_distribution(cls, dataset_id: str) -> DistributionResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        multipliers = [r.multiplier for r in rounds]
        return DistributionEngine.compute(dataset_id, multipliers)

    @classmethod
    async def get_rolling_stats(cls, dataset_id: str, window_size: int = 50) -> RollingStatsResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        return RollingEngine.compute(dataset_id, rounds, window_size=window_size)

    @classmethod
    async def get_autocorrelation(cls, dataset_id: str, max_lags: int = 15) -> AutocorrelationResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        sorted_r = sorted(rounds, key=lambda x: x.round_timestamp)
        multipliers = [r.multiplier for r in sorted_r]
        return IndependenceEngine.compute(dataset_id, multipliers, max_lags=max_lags)

    @classmethod
    async def get_outliers(cls, dataset_id: str) -> OutlierResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        return OutlierEngine.compute(dataset_id, rounds)

    @classmethod
    async def get_drift(
        cls,
        dataset_id: str,
        baseline_window: int = 100,
        comparison_window: int = 100
    ) -> DriftComparisonResponse:
        rounds = await dataset_manager.get_dataset_rounds(dataset_id)
        sorted_r = sorted(rounds, key=lambda x: x.round_timestamp)
        multipliers = [r.multiplier for r in sorted_r]
        return DriftEngine.compare_windows(
            dataset_id,
            multipliers,
            baseline_window=baseline_window,
            comparison_window=comparison_window
        )

    @classmethod
    async def compare_platforms(
        cls,
        dataset_a_id: str,
        dataset_b_id: str
    ) -> CrossPlatformComparisonResponse:
        rounds_a = await dataset_manager.get_dataset_rounds(dataset_a_id)
        rounds_b = await dataset_manager.get_dataset_rounds(dataset_b_id)

        mults_a = [r.multiplier for r in rounds_a]
        mults_b = [r.multiplier for r in rounds_b]

        mean_a = round(float(np.mean(mults_a)), 4) if mults_a else None
        mean_b = round(float(np.mean(mults_b)), 4) if mults_b else None
        med_a = round(float(np.median(mults_a)), 4) if mults_a else None
        med_b = round(float(np.median(mults_b)), 4) if mults_b else None

        p_val = None
        d_stat = 0.0
        if len(mults_a) >= 5 and len(mults_b) >= 5:
            ks_res = stats.ks_2samp(mults_a, mults_b)
            p_val = round(float(ks_res.pvalue), 5)
            d_stat = round(float(ks_res.statistic), 4)

        status = "COMPATIBLE_ANALYSIS" if (p_val and p_val > 0.05) else "DIVERGENT_DISTRIBUTIONS"

        return CrossPlatformComparisonResponse(
            platform_a=dataset_a_id,
            platform_b=dataset_b_id,
            sample_a=len(mults_a),
            sample_b=len(mults_b),
            mean_a=mean_a,
            mean_b=mean_b,
            median_a=med_a,
            median_b=med_b,
            ks_pvalue=p_val,
            divergence_score=d_stat,
            status=status
        )


analytics_service = AnalyticsService()

