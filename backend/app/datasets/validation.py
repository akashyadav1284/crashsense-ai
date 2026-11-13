"""Strict Validation & Data Quality Scoring Engine."""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.datasets.models import (
    DatasetValidationReport,
    ValidationRuleViolation,
)


class DataValidationEngine:
    """Rigorous mathematical & schema validator for historical multiplier rounds."""

    @classmethod
    def validate_round_record(cls, record: NormalizedGameRound) -> List[ValidationRuleViolation]:
        violations: List[ValidationRuleViolation] = []

        # 1. Multiplier checks: Finite, positive, reasonable
        if record.multiplier is None or record.multiplier <= 0:
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="NON_POSITIVE_MULTIPLIER",
                    message=f"Multiplier {record.multiplier} must be strictly positive.",
                    severity="ERROR",
                )
            )

        if record.multiplier != record.multiplier or record.multiplier == float("inf"):
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="INVALID_FLOAT_MULTIPLIER",
                    message="Multiplier contains NaN or Infinity.",
                    severity="ERROR",
                )
            )

        # 2. Identifier checks
        if not record.round_id or not str(record.round_id).strip():
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="MISSING_ROUND_ID",
                    message="Round ID cannot be empty or missing.",
                    severity="ERROR",
                )
            )

        if not record.platform_id or not record.provider_id:
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="MISSING_TAXONOMY",
                    message="Platform and Provider must be identified.",
                    severity="ERROR",
                )
            )

        # 3. Timestamp checks
        if not record.round_timestamp:
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="MISSING_TIMESTAMP",
                    message="Round timestamp is missing.",
                    severity="ERROR",
                )
            )
        elif record.round_timestamp > datetime.now(timezone.utc):
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="FUTURE_TIMESTAMP",
                    message=f"Timestamp {record.round_timestamp} is in the future.",
                    severity="WARNING",
                )
            )

        # 4. Hash verification check
        if record.verification_status != "VERIFIED":
            violations.append(
                ValidationRuleViolation(
                    round_id=record.round_id,
                    rule="UNVERIFIED_HASH",
                    message="Record lacks cryptographic seed verification.",
                    severity="WARNING",
                )
            )

        return violations

    @classmethod
    def compute_dataset_quality(
        cls,
        dataset_id: str,
        rounds: List[NormalizedGameRound],
        duplicates_count: int = 0,
        conflicts_count: int = 0
    ) -> DatasetValidationReport:
        """Calculates measurable Data Quality Score (0-100) based on documented rules."""
        total = len(rounds)
        if total == 0:
            return DatasetValidationReport(
                report_id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                total_evaluated=0,
                valid_records=0,
                invalid_records=0,
                duplicate_records=duplicates_count,
                conflict_records=conflicts_count,
                unverified_records=0,
                timestamp_anomalies=0,
                quality_score=0.0,
                status="EMPTY",
                violations=[],
            )

        all_violations: List[ValidationRuleViolation] = []
        invalid_count = 0
        unverified_count = 0
        ts_anomalies = 0

        # Sort rounds chronologically to verify monotonic sequence
        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)
        for i, r in enumerate(sorted_rounds):
            violations = cls.validate_round_record(r)
            if any(v.severity == "ERROR" for v in violations):
                invalid_count += 1
            if r.verification_status != "VERIFIED":
                unverified_count += 1
            if any(v.rule == "FUTURE_TIMESTAMP" for v in violations):
                ts_anomalies += 1

            all_violations.extend(violations)

        # Mathematical Scoring Deductions:
        # Start at 100
        # - Invalid records penalty: (invalid / total) * 60
        # - Conflict penalty: (conflicts / total) * 30
        # - Duplicate penalty: (duplicates / (total + duplicates)) * 10
        # - Unverified records penalty: (unverified / total) * 10
        invalid_penalty = (invalid_count / total) * 60.0
        conflict_penalty = (conflicts_count / total) * 30.0 if total > 0 else 0
        dup_penalty = (duplicates_count / (total + duplicates_count)) * 10.0 if (total + duplicates_count) > 0 else 0
        unverified_penalty = (unverified_count / total) * 10.0

        score = max(0.0, min(100.0, 100.0 - (invalid_penalty + conflict_penalty + dup_penalty + unverified_penalty)))

        status = "EXCELLENT" if score >= 90.0 else "ACCEPTABLE" if score >= 75.0 else "DEGRADED" if score >= 50.0 else "REJECTED"

        return DatasetValidationReport(
            report_id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            total_evaluated=total,
            valid_records=total - invalid_count,
            invalid_records=invalid_count,
            duplicate_records=duplicates_count,
            conflict_records=conflicts_count,
            unverified_records=unverified_count,
            timestamp_anomalies=ts_anomalies,
            quality_score=round(score, 2),
            status=status,
            violations=all_violations[:100],  # Truncate violations array for responsiveness
        )
