"""Multiplier Distribution & Wilson Confidence Intervals."""
import math
from typing import List, Dict, Any, Tuple
import numpy as np
from backend.app.analytics.schemas.analytics import (
    DistributionResponse,
    CategoryFrequencyItem,
)


class DistributionEngine:
    """Computes categorical frequency distributions with Wilson score confidence intervals."""

    DEFAULT_BINS = [
        ("1.00x-1.49x", 1.00, 1.49),
        ("1.50x-1.99x", 1.50, 1.99),
        ("2.00x-4.99x", 2.00, 4.99),
        ("5.00x-9.99x", 5.00, 9.99),
        ("10.00x-19.99x", 10.00, 19.99),
        ("20.00x-49.99x", 20.00, 49.99),
        ("50.00x-99.99x", 50.00, 99.99),
        ("100.00x+", 100.00, float("inf")),
    ]

    @staticmethod
    def wilson_score_interval(count: int, n: int, confidence: float = 0.95) -> List[float]:
        """Calculates exact Wilson score confidence interval for a binomial proportion."""
        if n == 0:
            return [0.0, 0.0]

        z = 1.95996  # 95% two-sided normal quantile
        p_hat = count / n
        denominator = 1 + (z ** 2) / n
        center = (p_hat + (z ** 2) / (2 * n)) / denominator
        spread = (z / denominator) * math.sqrt((p_hat * (1 - p_hat) / n) + (z ** 2) / (4 * (n ** 2)))
        lower = max(0.0, center - spread)
        upper = min(1.0, center + spread)
        return [round(lower, 4), round(upper, 4)]

    @classmethod
    def compute(
        cls,
        dataset_id: str,
        data: List[float],
        custom_bins: List[Tuple[str, float, float]] = None
    ) -> DistributionResponse:
        n = len(data)
        if n == 0:
            return DistributionResponse(dataset_id=dataset_id, sample_size=0, categories=[])

        arr = np.array(data, dtype=np.float64)
        bins = custom_bins or cls.DEFAULT_BINS

        categories: List[CategoryFrequencyItem] = []
        cumulative_count = 0

        for label, low, high in bins:
            if math.isinf(high):
                count = int(np.sum(arr >= low))
            else:
                count = int(np.sum((arr >= low) & (arr <= high + 0.0099)))

            cumulative_count += count
            rel_freq = round(count / n, 4)
            cum_rel_freq = round(cumulative_count / n, 4)
            ci = cls.wilson_score_interval(count, n, confidence=0.95)

            categories.append(
                CategoryFrequencyItem(
                    category=label,
                    range_min=low,
                    range_max=high if not math.isinf(high) else 999999.0,
                    count=count,
                    relative_frequency=rel_freq,
                    cumulative_count=cumulative_count,
                    cumulative_relative_frequency=cum_rel_freq,
                    confidence_interval=ci
                )
            )

        return DistributionResponse(
            dataset_id=dataset_id,
            sample_size=n,
            categories=categories
        )

