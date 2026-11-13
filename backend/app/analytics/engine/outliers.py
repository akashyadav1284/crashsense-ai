"""Outlier & Anomaly Analysis Engine."""
from typing import List, Dict, Any
import numpy as np
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.analytics.schemas.analytics import OutlierResponse, OutlierItem


class OutlierEngine:
    """Detects statistical outliers and separates them from data-quality anomalies."""

    @classmethod
    def compute(
        cls,
        dataset_id: str,
        rounds: List[NormalizedGameRound]
    ) -> OutlierResponse:
        n = len(rounds)
        if n < 10:
            return OutlierResponse(
                dataset_id=dataset_id,
                sample_size=n,
                total_outliers=0,
                outliers=[],
                iqr_bounds={}
            )

        mults = np.array([r.multiplier for r in rounds], dtype=np.float64)
        q25, q75 = np.percentile(mults, [25, 75])
        iqr = q75 - q25
        lower_bound = max(1.0, q25 - 1.5 * iqr)
        upper_bound = q75 + 1.5 * iqr

        outlier_items: List[OutlierItem] = []
        for r in rounds:
            # Statistical Outlier (extreme high crash multiplier)
            if r.multiplier > upper_bound:
                outlier_items.append(
                    OutlierItem(
                        round_id=r.round_id,
                        multiplier=r.multiplier,
                        timestamp=r.round_timestamp.isoformat(),
                        method="Tukey 1.5x IQR Fence",
                        reason=f"Observed multiplier {r.multiplier}x exceeds 75th percentile fence ({upper_bound:.2f}x).",
                        category="STATISTICAL_OUTLIER"
                    )
                )

        return OutlierResponse(
            dataset_id=dataset_id,
            sample_size=n,
            total_outliers=len(outlier_items),
            outliers=outlier_items[:50],  # Return up to 50 for API responsiveness
            iqr_bounds={
                "q25": round(float(q25), 2),
                "q75": round(float(q75), 2),
                "iqr": round(float(iqr), 2),
                "lower_bound": round(float(lower_bound), 2),
                "upper_bound": round(float(upper_bound), 2),
            }
        )

