"""Zero-Leakage Feature and Target Builder."""
import math
from typing import List, Tuple, Dict, Any, Union
import numpy as np
import pandas as pd
from backend.app.connectors.schemas.round import NormalizedGameRound


class FeatureBuilder:
    """Builds strictly backward-looking lag and rolling features with zero lookahead leakage."""

    LAG_STEPS = [1, 2, 3, 5, 10]
    ROLLING_WINDOWS = [10, 25, 50]

    @classmethod
    def build_matrix(
        cls,
        rounds: List[NormalizedGameRound],
        target_type: str = "binary_above_2x"
    ) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Extracts strictly lagged features X and forward target y from NormalizedGameRound list."""
        if len(rounds) < 20:
            raise ValueError(f"Insufficient samples: {len(rounds)} rounds. Minimum 20 required.")

        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)
        df = pd.DataFrame([
            {
                "round_id": r.round_id,
                "timestamp": r.round_timestamp,
                "multiplier": r.multiplier,
            }
            for r in sorted_rounds
        ])
        target_threshold = 1.5 if target_type == "binary_above_1.5x" else 2.0
        X_arr, y_arr, f_names = cls.build_features(df, target_threshold=target_threshold, min_history=25)
        return pd.DataFrame(X_arr, columns=f_names), pd.Series(y_arr), f_names

    @classmethod
    def build_features(
        cls,
        df_rounds: pd.DataFrame,
        target_threshold: float = 2.0,
        min_history: int = 25
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Extracts strictly lagged features X and forward target y from DataFrame.
        Zero-Leakage Rule:
        Row t contains:
          - X[t]: Features computed strictly from rounds up to t-1
          - y[t]: Target label defined on round t's outcome (multiplier >= target_threshold)
        """
        if len(df_rounds) < min_history:
            raise ValueError(f"Insufficient samples: {len(df_rounds)} rounds. Minimum {min_history} required.")

        df = df_rounds.copy()
        if "timestamp" in df.columns:
            df.sort_values(by="timestamp", ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        multipliers = df["multiplier"].values

        # 1. Target Construction at index t
        y = (multipliers >= target_threshold).astype(int)

        # 2. Backward-looking features for row t from history [:t]
        feature_rows: List[Dict[str, float]] = []

        # Windows to use, constrained by min_history
        windows = [w for w in cls.ROLLING_WINDOWS if w <= min_history]
        if not windows:
            windows = [min(10, min_history)]

        for t in range(min_history, len(multipliers)):
            # History strictly strictly before t: multipliers[0:t]
            hist = multipliers[:t]
            row_dict: Dict[str, float] = {}

            # Lags
            for lag in cls.LAG_STEPS:
                val = hist[-lag] if len(hist) >= lag else hist[-1]
                row_dict[f"lag_{lag}_mult"] = float(val)
                row_dict[f"lag_{lag}_log"] = float(np.log(max(1.0, val)))

            # Rolling stats on shifted history
            for w in windows:
                w_hist = hist[-w:] if len(hist) >= w else hist
                row_dict[f"roll_{w}_mean"] = float(np.mean(w_hist))
                row_dict[f"roll_{w}_median"] = float(np.median(w_hist))
                row_dict[f"roll_{w}_std"] = float(np.std(w_hist))
                row_dict[f"roll_{w}_min"] = float(np.min(w_hist))
                row_dict[f"roll_{w}_max"] = float(np.max(w_hist))
                row_dict[f"roll_{w}_p_gt_target"] = float(np.mean(w_hist >= target_threshold))

            # Streak of consecutive rounds below target threshold immediately prior to t
            streak = 0
            for k in range(1, len(hist) + 1):
                if hist[-k] < target_threshold:
                    streak += 1
                else:
                    break
            row_dict["streak_below_target"] = float(streak)

            feature_rows.append(row_dict)

        feature_names = sorted(list(feature_rows[0].keys()))
        X = np.array([[row[f_name] for f_name in feature_names] for row in feature_rows], dtype=float)
        y_aligned = y[min_history:]

        return X, y_aligned, feature_names

    @classmethod
    def _compute_streak_at_idx(cls, arr: np.ndarray, idx: int, threshold: float) -> int:
        """Helper to compute streak of rounds below threshold up to index."""
        streak = 0
        for i in range(idx, -1, -1):
            if arr[i] < threshold:
                streak += 1
            else:
                break
        return streak
