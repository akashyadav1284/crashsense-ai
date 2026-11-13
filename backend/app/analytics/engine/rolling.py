"""Rolling Windows Statistical Moments Engine."""
import math
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.analytics.schemas.analytics import RollingStatsResponse, RollingPoint


class RollingEngine:
    """Calculates continuous rolling window metrics with minimum sample requirements."""

    SUPPORTED_WINDOWS = [10, 25, 50, 100, 250, 500, 1000]

    @classmethod
    def compute(
        cls,
        dataset_id: str,
        rounds: List[NormalizedGameRound],
        window_size: int = 50
    ) -> RollingStatsResponse:
        n = len(rounds)
        if n < window_size or window_size <= 0:
            return RollingStatsResponse(
                dataset_id=dataset_id,
                window_size=window_size,
                total_points=0,
                series=[],
                notice=f"Dataset has {n} records. A minimum of {window_size} chronological rounds is required."
            )

        # Ensure strict chronological order
        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)
        df = pd.DataFrame([
            {
                "round_id": r.round_id,
                "timestamp": r.round_timestamp.isoformat(),
                "multiplier": r.multiplier
            }
            for r in sorted_rounds
        ])

        # Rolling calculations using Pandas vectorized methods
        roll = df["multiplier"].rolling(window=window_size, min_periods=window_size)
        df["mean"] = roll.mean()
        df["median"] = roll.median()
        df["std"] = roll.std().fillna(0.0)
        df["min"] = roll.min()
        df["max"] = roll.max()

        valid_df = df.dropna(subset=["mean"]).reset_index(drop=True)
        series_points = []
        for _, row in valid_df.iterrows():
            series_points.append(
                RollingPoint(
                    round_id=row["round_id"],
                    timestamp=row["timestamp"],
                    rolling_mean=round(float(row["mean"]), 4),
                    rolling_median=round(float(row["median"]), 4),
                    rolling_std=round(float(row["std"]), 4),
                    rolling_min=round(float(row["min"]), 4),
                    rolling_max=round(float(row["max"]), 4),
                    observed_multiplier=round(float(row["multiplier"]), 4)
                )
            )

        return RollingStatsResponse(
            dataset_id=dataset_id,
            window_size=window_size,
            total_points=len(series_points),
            series=series_points[-200:]  # Return most recent 200 points for UI performance
        )

