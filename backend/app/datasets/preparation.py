"""Dataset Slicing, Rolling Window Extraction, and Category Mapping."""
from typing import List, Dict, Any, Optional
import math
from backend.app.connectors.schemas.round import NormalizedGameRound


class DataAnalysisPreparation:
    """Prepares chronological historical datasets for research & modeling without predicting."""

    @staticmethod
    def categorize_multiplier(multiplier: float) -> str:
        """Map raw continuous multiplier to standard volatility bins."""
        if multiplier < 1.50:
            return "1.00x-1.49x"
        elif multiplier < 2.00:
            return "1.50x-1.99x"
        elif multiplier < 5.00:
            return "2.00x-4.99x"
        elif multiplier < 10.00:
            return "5.00x-9.99x"
        elif multiplier < 20.00:
            return "10.00x-19.99x"
        else:
            return "20.00x+"

    @classmethod
    def extract_rolling_windows(
        cls,
        rounds: List[NormalizedGameRound],
        window_size: int = 50
    ) -> List[Dict[str, Any]]:
        """Extracts rolling empirical means, medians, and variance slices over chronologically sorted rounds."""
        if len(rounds) < window_size:
            return []

        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)
        results = []
        mults = [r.multiplier for r in sorted_rounds]

        for i in range(window_size, len(mults) + 1):
            window = mults[i - window_size:i]
            mean_val = sum(window) / window_size
            sorted_win = sorted(window)
            median_val = sorted_win[window_size // 2]
            var_val = sum((x - mean_val) ** 2 for x in window) / window_size
            std_val = math.sqrt(var_val)

            results.append({
                "round_id": sorted_rounds[i - 1].round_id,
                "timestamp": sorted_rounds[i - 1].round_timestamp.isoformat(),
                "window_size": window_size,
                "rolling_mean": round(mean_val, 4),
                "rolling_median": round(median_val, 4),
                "rolling_std": round(std_val, 4),
                "observed_multiplier": sorted_rounds[i - 1].multiplier,
                "category": cls.categorize_multiplier(sorted_rounds[i - 1].multiplier)
            })

        return results

    @classmethod
    def prepare_feature_ready_matrix(
        cls,
        rounds: List[NormalizedGameRound]
    ) -> List[Dict[str, Any]]:
        """Converts raw canonical rounds to structured feature dicts for Phase 5 ML baselines."""
        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)
        records = []
        for r in sorted_rounds:
            records.append({
                "round_id": r.round_id,
                "timestamp": r.round_timestamp.isoformat(),
                "multiplier": r.multiplier,
                "log_multiplier": round(math.log(max(1.0, r.multiplier)), 4),
                "category": cls.categorize_multiplier(r.multiplier),
                "verified": (r.verification_status == "VERIFIED"),
                "source": r.source_type
            })
        return records
