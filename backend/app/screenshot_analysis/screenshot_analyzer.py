"""Statistical analysis wrapper tailored for screenshot-extracted Aviator series."""
import math
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from backend.app.screenshot_analysis.schemas import MultiplierRecord, StatisticalSummary


class ScreenshotAnalyzer:
    """Executes descriptive statistics, rolling averages, and independence tests on screenshot sequences."""

    @classmethod
    def calculate_statistics(cls, records: List[MultiplierRecord]) -> StatisticalSummary:
        """Computes statistical metrics over confirmed multiplier sequence."""
        multipliers = [r.multiplier for r in records if r.multiplier and r.multiplier >= 1.0]
        n = len(multipliers)
        if n == 0:
            raise ValueError("No valid multipliers available for statistical analysis.")

        arr = np.array(multipliers, dtype=np.float64)

        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))

        # Categorical breakdown
        # 1: < 1.50x
        # 2: 1.50 - 1.99x
        # 3: 2.00 - 4.99x
        # 4: 5.00 - 9.99x
        # 5: >= 10.00x
        c1 = int(np.sum(arr < 1.50))
        c2 = int(np.sum((arr >= 1.50) & (arr < 2.00)))
        c3 = int(np.sum((arr >= 2.00) & (arr < 5.00)))
        c4 = int(np.sum((arr >= 5.00) & (arr < 10.00)))
        c5 = int(np.sum(arr >= 10.00))

        frequencies = {
            "below_1_50x": c1,
            "1_50x_to_1_99x": c2,
            "2_00x_to_4_99x": c3,
            "5_00x_to_9_99x": c4,
            "10_00x_and_above": c5,
        }

        percentages = {
            "below_1_50x": round((c1 / n) * 100.0, 2),
            "1_50x_to_1_99x": round((c2 / n) * 100.0, 2),
            "2_00x_to_4_99x": round((c3 / n) * 100.0, 2),
            "5_00x_to_9_99x": round((c4 / n) * 100.0, 2),
            "10_00x_and_above": round((c5 / n) * 100.0, 2),
        }

        # Rolling average (window = min(5, n))
        window = min(5, n)
        rolling_averages = []
        for i in range(n):
            start_idx = max(0, i - window + 1)
            subset = arr[start_idx: i + 1]
            rolling_averages.append(round(float(np.mean(subset)), 2))

        # Autocorrelation Lag 1
        autocorr_lag1 = None
        if n >= 10:
            y = arr - mean_val
            var = np.sum(y ** 2)
            if var > 0:
                autocorr_lag1 = round(float(np.sum(y[:-1] * y[1:]) / var), 3)

        # Wald-Wolfowitz Runs Test for independence around median
        runs_p_value = None
        independence_detected = None
        if n >= 15:
            # Binary sequence: above median vs below median
            binary_seq = (arr >= median_val).astype(int)
            runs = 1 + np.sum(binary_seq[1:] != binary_seq[:-1])
            n1 = np.sum(binary_seq == 1)
            n2 = np.sum(binary_seq == 0)

            if n1 > 0 and n2 > 0:
                mu_r = ((2 * n1 * n2) / (n1 + n2)) + 1
                var_r = ((2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (((n1 + n2) ** 2) * (n1 + n2 - 1)))
                if var_r > 0:
                    z = (runs - mu_r) / math.sqrt(var_r)
                    runs_p_value = round(float(2 * (1 - stats.norm.cdf(abs(z)))), 4)
                    # If p > 0.05, cannot reject null hypothesis of independence
                    independence_detected = bool(runs_p_value >= 0.05)

        return StatisticalSummary(
            sample_size=n,
            mean=round(mean_val, 2),
            median=round(median_val, 2),
            std_dev=round(std_val, 2),
            min_multiplier=round(min_val, 2),
            max_multiplier=round(max_val, 2),
            frequencies=frequencies,
            percentages=percentages,
            rolling_averages=rolling_averages,
            autocorrelation_lag1=autocorr_lag1,
            runs_test_p_value=runs_p_value,
            independence_detected=independence_detected,
        )
