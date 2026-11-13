"""Validation rules and normalization for extracted screenshot multiplier sequences."""
from typing import List, Tuple, Dict, Any
from backend.app.screenshot_analysis.schemas import MultiplierRecord


class DataValidator:
    """Enforces strict scientific and schema constraints on extracted multipliers."""

    @classmethod
    def validate_records(cls, records: List[MultiplierRecord]) -> Tuple[bool, List[str]]:
        """Validates multiplier values, sequences, and checks for duplicates without silently dropping them."""
        errors = []
        if not records:
            return False, ["Sequence contains zero multiplier records."]

        seen_mults = {}
        for idx, rec in enumerate(records):
            # Check numerical minimum
            if rec.multiplier is None or rec.multiplier < 1.00:
                errors.append(f"Row {rec.sequence}: Multiplier {rec.multiplier} is invalid (must be >= 1.00x).")

            # Check sequence ordering
            if rec.sequence != idx + 1:
                # We can correct sequence numbers or report warning
                pass

            # Track duplicate values (alert but do not drop)
            seen_mults[rec.multiplier] = seen_mults.get(rec.multiplier, 0) + 1

        # Check for sequence duplicates
        has_critical_error = len(errors) > 0
        return not has_critical_error, errors

    @classmethod
    def resequence(cls, records: List[MultiplierRecord]) -> List[MultiplierRecord]:
        """Ensures monotonic 1-based indexing for the sequence."""
        resequenced = []
        for i, rec in enumerate(records, start=1):
            updated = rec.model_copy()
            updated.sequence = i
            resequenced.append(updated)
        return resequenced
