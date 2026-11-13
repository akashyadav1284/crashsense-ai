"""Distribution Drift & Two-Sample Nonparametric Comparison Engine."""
import math
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats
from backend.app.analytics.schemas.analytics import (
    DriftComparisonResponse,
    IndependenceTestResult,
)


class DriftEngine:
    """Computes distribution stability across chronological windows using KS-test and PSI."""

    @staticmethod
    def calculate_psi(baseline: np.ndarray, target: np.ndarray, num_bins: int = 10) -> float:
        """Calculates Population Stability Index (PSI) with quantile binning."""
        if len(baseline) == 0 or len(target) == 0:
            return 0.0

        quantiles = np.linspace(0, 100, num_bins + 1)
        bin_edges = np.percentile(baseline, quantiles)
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        base_counts, _ = np.histogram(baseline, bins=bin_edges)
        target_counts, _ = np.histogram(target, bins=bin_edges)

        base_pct = base_counts / len(baseline)
        target_pct = target_counts / len(target)

        # Apply Laplace epsilon to prevent division by zero or log(0)
        eps = 1e-4
        base_pct = np.where(base_pct == 0, eps, base_pct)
        target_pct = np.where(target_pct == 0, eps, target_pct)

        psi = np.sum((target_pct - base_pct) * np.log(target_pct / base_pct))
        return round(float(psi), 4)

    @classmethod
    def compare_windows(
        cls,
        dataset_id: str,
        chronological_multipliers: List[float],
        baseline_window: int = 100,
        comparison_window: int = 100
    ) -> DriftComparisonResponse:
        total_needed = baseline_window + comparison_window
        n = len(chronological_multipliers)

        if n < total_needed:
            # Fallback for small sample
            half = n // 2
            baseline_window = max(5, half)
            comparison_window = max(5, half)

        arr = np.array(chronological_multipliers, dtype=np.float64)
        base_slice = arr[-(baseline_window + comparison_window):-comparison_window]
        target_slice = arr[-comparison_window:]

        if len(base_slice) < 5 or len(target_slice) < 5:
            return DriftComparisonResponse(
                dataset_id=dataset_id,
                baseline_window=len(base_slice),
                comparison_window=len(target_slice),
                ks_test=IndependenceTestResult(
                    test_name="Two-Sample Kolmogorov-Smirnov Test",
                    null_hypothesis="Both sample windows originate from identical continuous distributions.",
                    alternative_hypothesis="Cumulative distribution functions differ.",
                    test_statistic=0.0,
                    p_value=1.0,
                    sample_size=n,
                    reject_null=False,
                    interpretation="Insufficient sample count to evaluate distribution drift.",
                    limitations="Requires minimum 20 rounds per comparison partition."
                ),
                wasserstein_distance=0.0,
                psi_score=0.0,
                drift_status="INSUFFICIENT_DATA"
            )

        # 1. Two-sample Kolmogorov-Smirnov Test
        ks_res = stats.ks_2samp(base_slice, target_slice)
        d_stat = float(ks_res.statistic)
        p_val = float(ks_res.pvalue)

        # 2. Wasserstein Distance (Earth Mover's Distance)
        w_dist = float(stats.wasserstein_distance(base_slice, target_slice))

        # 3. Population Stability Index
        psi = cls.calculate_psi(base_slice, target_slice)

        reject = bool(p_val < 0.05)
        drift_status = "SIGNIFICANT_DRIFT" if (reject and psi > 0.25) else "MODERATE_DRIFT" if (psi > 0.10) else "NO_DRIFT"

        ks_model = IndependenceTestResult(
            test_name="Two-Sample Kolmogorov-Smirnov Test for Concept Drift",
            null_hypothesis="The baseline window and comparison window share identical continuous multiplier distributions.",
            alternative_hypothesis="Empirical distributions differ significantly.",
            test_statistic=round(d_stat, 4),
            p_value=round(p_val, 5),
            sample_size=len(base_slice) + len(target_slice),
            reject_null=reject,
            interpretation=(
                "Statistically significant divergence detected between historical windows."
                if reject
                else "No significant distribution drift detected between the sequential windows."
            ),
            limitations="Sensitive to extreme right-tail multiplier variance in small sample sizes."
        )

        return DriftComparisonResponse(
            dataset_id=dataset_id,
            baseline_window=len(base_slice),
            comparison_window=len(target_slice),
            ks_test=ks_model,
            wasserstein_distance=round(w_dist, 4),
            psi_score=psi,
            drift_status=drift_status
        )

