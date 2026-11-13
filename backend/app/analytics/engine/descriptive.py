"""Descriptive & Percentile Moments Calculations."""
import math
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from backend.app.analytics.schemas.analytics import DescriptiveStatsResponse


class DescriptiveEngine:
    """Computes sample moments, robust spread metrics, and percentiles."""

    @classmethod
    def compute(cls, dataset_id: str, data: List[float]) -> DescriptiveStatsResponse:
        if not data:
            return DescriptiveStatsResponse(
                dataset_id=dataset_id,
                sample_size=0,
                warning="Dataset contains 0 records. Descriptive statistics cannot be computed."
            )

        arr = np.array(data, dtype=np.float64)
        n = len(arr)

        if n < 3:
            return DescriptiveStatsResponse(
                dataset_id=dataset_id,
                sample_size=n,
                mean=round(float(np.mean(arr)), 4),
                median=round(float(np.median(arr)), 4),
                min=round(float(np.min(arr)), 4),
                max=round(float(np.max(arr)), 4),
                warning="Sample size N < 3 is insufficient for variance and higher-order moment estimations."
            )

        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        range_val = max_val - min_val
        var_val = float(np.var(arr, ddof=1))
        std_val = float(np.std(arr, ddof=1))
        cv_val = std_val / mean_val if mean_val != 0 else 0.0

        # Skewness & Kurtosis
        skew_val = float(stats.skew(arr))
        kurt_val = float(stats.kurtosis(arr))  # Fisher's definition (normal = 0)

        # Percentiles
        pct_keys = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        pct_values = np.percentile(arr, pct_keys)
        percentiles_dict = {f"P{k}": round(float(v), 4) for k, v in zip(pct_keys, pct_values)}

        iqr_val = percentiles_dict["P75"] - percentiles_dict["P25"]

        # Approximate Mode
        try:
            m_res = stats.mode(np.round(arr, 2), keepdims=False)
            mode_val = round(float(m_res.mode), 2)
        except Exception:
            mode_val = None

        return DescriptiveStatsResponse(
            dataset_id=dataset_id,
            sample_size=n,
            missing_count=0,
            mean=round(mean_val, 4),
            median=round(median_val, 4),
            mode=mode_val,
            min=round(min_val, 4),
            max=round(max_val, 4),
            range=round(range_val, 4),
            variance=round(var_val, 4),
            std_dev=round(std_val, 4),
            skewness=round(skew_val, 4),
            kurtosis=round(kurt_val, 4),
            iqr=round(iqr_val, 4),
            coefficient_of_variation=round(cv_val, 4),
            percentiles=percentiles_dict
        )

