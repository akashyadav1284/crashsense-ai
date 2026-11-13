"""Stateful analysis coordinator and persistence service."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from backend.app.screenshot_analysis.schemas import (
    ScreenshotAnalysisResponse,
    ExtractionStatus,
    AnalysisStatus,
    MultiplierRecord,
    MultiplierCorrectionUpdate,
    MultiplierVerificationConfirm,
)
from backend.app.screenshot_analysis.ocr_engine import OCREngine
from backend.app.screenshot_analysis.data_validator import DataValidator
from backend.app.screenshot_analysis.screenshot_analyzer import ScreenshotAnalyzer
from backend.app.screenshot_analysis.prediction_service import PredictionService
from backend.app.datasets.manager import dataset_manager
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.core.logging import logger


class AnalysisService:
    """Manages screenshot lifecycle: upload, OCR, user correction, confirmation, and statistical/ML analysis."""

    def __init__(self):
        # In-memory storage for rapid session analysis, paired with DB queries
        self._analyses: Dict[str, ScreenshotAnalysisResponse] = {}
        self._image_store: Dict[str, bytes] = {}

    async def create_analysis(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> ScreenshotAnalysisResponse:
        """Stores image upload and initializes analysis entity."""
        analysis_id = f"sa_{uuid.uuid4().hex[:12]}"

        # Validate image format immediately
        records, raw_text, quality_score = OCREngine.process_screenshot(file_bytes)

        # Convert extracted dicts to MultiplierRecords
        extracted_models = []
        for idx, rec in enumerate(records, start=1):
            extracted_models.append(
                MultiplierRecord(
                    sequence=idx,
                    multiplier=rec["multiplier"],
                    ocr_confidence=rec.get("confidence", 0.85),
                    round_id=rec.get("round_id"),
                    timestamp=None,
                    source="SCREENSHOT_OCR",
                    verification_status="UNVERIFIED",
                    is_flagged=False,
                    raw_ocr_text=rec.get("raw_token"),
                )
            )

        status = ExtractionStatus.EXTRACTED if extracted_models else ExtractionStatus.FAILED

        analysis_obj = ScreenshotAnalysisResponse(
            id=analysis_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size_bytes=len(file_bytes),
            upload_timestamp=datetime.now(timezone.utc),
            extraction_status=status,
            analysis_status=AnalysisStatus.IDLE,
            extracted_records=extracted_models,
            user_confirmed_records=[],
            data_quality_score=quality_score,
            notes=f"Raw OCR identified {len(extracted_models)} potential multiplier tokens.",
        )

        self._analyses[analysis_id] = analysis_obj
        self._image_store[analysis_id] = file_bytes
        return analysis_obj

    async def get_analysis(self, analysis_id: str, user_id: str) -> Optional[ScreenshotAnalysisResponse]:
        """Retrieves analysis record enforcing user tenant isolation."""
        analysis = self._analyses.get(analysis_id)
        if not analysis:
            return None
        if analysis.user_id != user_id:
            return None
        return analysis

    async def list_history(self, user_id: str) -> List[ScreenshotAnalysisResponse]:
        """Lists past screenshot analyses for the specified user."""
        return [a for a in self._analyses.values() if a.user_id == user_id]

    async def correct_data(
        self,
        analysis_id: str,
        user_id: str,
        update_data: MultiplierCorrectionUpdate,
    ) -> ScreenshotAnalysisResponse:
        """Applies manual user edits or sequence reorderings."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            raise KeyError("Analysis not found or permission denied.")

        valid, errs = DataValidator.validate_records(update_data.records)
        if not valid:
            raise ValueError("; ".join(errs))

        # Re-sequence 1-based order
        resequenced = DataValidator.resequence(update_data.records)
        analysis.extracted_records = resequenced
        analysis.notes = f"User corrected {len(resequenced)} records."
        return analysis

    async def confirm_data(
        self,
        analysis_id: str,
        user_id: str,
        confirm_req: MultiplierVerificationConfirm,
    ) -> ScreenshotAnalysisResponse:
        """Locks in user verification and optionally creates a historical dataset."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            raise KeyError("Analysis not found or permission denied.")

        if not analysis.extracted_records:
            raise ValueError("Cannot confirm empty multiplier sequence.")

        confirmed = []
        for r in analysis.extracted_records:
            item = r.model_copy()
            item.verification_status = "USER_CONFIRMED"
            confirmed.append(item)

        analysis.user_confirmed_records = confirmed
        analysis.extraction_status = ExtractionStatus.CONFIRMED

        # If user requested to save to historical dataset engine:
        if confirm_req.save_to_historical_dataset:
            dataset_name = confirm_req.dataset_name or f"Screenshot Aviator - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
            normalized_rounds = []
            for item in confirmed:
                normalized_rounds.append(
                    NormalizedGameRound(
                        platform_id="spribe_aviator",
                        round_id=item.round_id or f"ocr_{uuid.uuid4().hex[:8]}",
                        crash_multiplier=item.multiplier,
                        timestamp=item.timestamp or datetime.now(timezone.utc),
                        raw_payload={"ocr_source": "SCREENSHOT_OCR", "confidence": item.ocr_confidence},
                    )
                )
            await dataset_manager.create_dataset(
                name=dataset_name,
                platform_id="spribe_aviator",
                rounds=normalized_rounds,
                notes=f"Derived from screenshot analysis ID {analysis_id}",
            )

        return analysis

    async def run_analysis(self, analysis_id: str, user_id: str) -> ScreenshotAnalysisResponse:
        """Executes statistical analytics and ML research estimate on confirmed records."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            raise KeyError("Analysis not found or permission denied.")

        if analysis.extraction_status != ExtractionStatus.CONFIRMED or not analysis.user_confirmed_records:
            raise ValueError("Multiplier records must be confirmed by the user before running analysis.")

        analysis.analysis_status = AnalysisStatus.ANALYZING

        # 1. Statistical Summary
        stats = ScreenshotAnalyzer.calculate_statistics(analysis.user_confirmed_records)
        analysis.statistics = stats

        # 2. Next-Round Research Estimate
        estimate = await PredictionService.evaluate_research_estimate(
            analysis.user_confirmed_records,
            stats,
        )
        analysis.research_estimate = estimate
        analysis.analysis_status = AnalysisStatus.COMPLETED

        return analysis

    async def delete_analysis(self, analysis_id: str, user_id: str) -> bool:
        """Deletes an analysis session and associated image bytes."""
        analysis = await self.get_analysis(analysis_id, user_id)
        if not analysis:
            return False
        self._analyses.pop(analysis_id, None)
        self._image_store.pop(analysis_id, None)
        return True


analysis_service = AnalysisService()
