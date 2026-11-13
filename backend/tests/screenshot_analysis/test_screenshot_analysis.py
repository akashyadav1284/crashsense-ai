"""Comprehensive test suite for screenshot-based Aviator OCR, validation, and estimation."""
import io
import pytest
from datetime import datetime, timezone
from PIL import Image, ImageDraw

from backend.app.screenshot_analysis.image_processor import ImageProcessor
from backend.app.screenshot_analysis.multiplier_extractor import MultiplierExtractor
from backend.app.screenshot_analysis.data_validator import DataValidator
from backend.app.screenshot_analysis.screenshot_analyzer import ScreenshotAnalyzer
from backend.app.screenshot_analysis.schemas import (
    MultiplierRecord,
    MultiplierCorrectionUpdate,
    MultiplierVerificationConfirm,
)
from backend.app.screenshot_analysis.analysis_service import analysis_service


def create_synthetic_screenshot(text_labels: list = None) -> bytes:
    """Generates a synthetic image containing multiplier labels for OCR testing."""
    if text_labels is None:
        text_labels = ["1.24x", "2.56x", "10.45x", "1.02x", "5.80x"]
    
    img = Image.new("RGB", (400, 200), color=(20, 24, 33))
    d = ImageDraw.Draw(img)
    # Draw simple shapes and text
    for i, txt in enumerate(text_labels):
        x = 20 + (i * 70)
        y = 40
        d.rectangle([x, y, x + 60, y + 30], fill=(45, 55, 72))
        d.text((x + 10, y + 8), txt, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_image_processor_validation():
    """Tests file size, format checks, and empty files."""
    valid_bytes = create_synthetic_screenshot()
    ok, msg, fmt = ImageProcessor.validate_image_bytes(valid_bytes, "test.png")
    assert ok is True
    assert fmt == "PNG"

    # Empty file
    ok, msg, fmt = ImageProcessor.validate_image_bytes(b"", "empty.png")
    assert ok is False

    # Invalid bytes
    ok, msg, fmt = ImageProcessor.validate_image_bytes(b"not an image", "fake.png")
    assert ok is False


def test_multiplier_extractor_regex():
    """Tests extraction of diverse multiplier tokens and rejection of balance texts."""
    raw_text = """
    AVIATOR LIVE
    History: 1.24x  2.56x  10.45x  100.00x  1,245.67x
    Account Balance: $10,500.00
    Bet Amount: 50.00 INR
    Cash Out: 2.10X
    """
    records = MultiplierExtractor.extract_multipliers_from_text(raw_text)
    mults = [r["multiplier"] for r in records]

    assert 1.24 in mults
    assert 2.56 in mults
    assert 10.45 in mults
    assert 100.0 in mults
    assert 1245.67 in mults
    assert 2.10 in mults
    # Ensure balance was not parsed as a multiplier
    assert 10500.0 not in mults


def test_data_validator_rules():
    """Tests schema validation, rejection of < 1.00x, and monotonic resequencing."""
    valid_recs = [
        MultiplierRecord(sequence=1, multiplier=1.50),
        MultiplierRecord(sequence=2, multiplier=2.20),
    ]
    ok, errs = DataValidator.validate_records(valid_recs)
    assert ok is True
    assert len(errs) == 0

    # Invalid multiplier < 1.0 (Testing Pydantic schema validation directly)
    with pytest.raises(Exception):
        MultiplierRecord(sequence=1, multiplier=0.95)

    # Resequencing
    messy_seq = [
        MultiplierRecord(sequence=5, multiplier=1.50),
        MultiplierRecord(sequence=2, multiplier=2.20),
    ]
    resequenced = DataValidator.resequence(messy_seq)
    assert resequenced[0].sequence == 1
    assert resequenced[1].sequence == 2


def test_screenshot_analyzer_statistics():
    """Tests descriptive moments, categorical distributions, and runs tests."""
    records = [
        MultiplierRecord(sequence=1, multiplier=1.20),
        MultiplierRecord(sequence=2, multiplier=1.80),
        MultiplierRecord(sequence=3, multiplier=2.50),
        MultiplierRecord(sequence=4, multiplier=6.00),
        MultiplierRecord(sequence=5, multiplier=15.00),
    ]
    summary = ScreenshotAnalyzer.calculate_statistics(records)

    assert summary.sample_size == 5
    assert summary.min_multiplier == 1.20
    assert summary.max_multiplier == 15.00
    assert summary.frequencies["below_1_50x"] == 1
    assert summary.frequencies["1_50x_to_1_99x"] == 1
    assert summary.frequencies["2_00x_to_4_99x"] == 1
    assert summary.frequencies["5_00x_to_9_99x"] == 1
    assert summary.frequencies["10_00x_and_above"] == 1
    assert len(summary.rolling_averages) == 5


@pytest.mark.asyncio
async def test_full_analysis_service_workflow():
    """Tests end-to-end service lifecycle: create -> correct -> confirm -> analyze -> delete."""
    fake_img = create_synthetic_screenshot()
    user_id = "test_user_screenshot"

    # 1. Create analysis
    analysis = await analysis_service.create_analysis(
        user_id=user_id,
        filename="aviator_test.png",
        content_type="image/png",
        file_bytes=fake_img,
    )
    assert analysis.id.startswith("sa_")
    assert analysis.user_id == user_id

    # 2. Add manual extracted records to simulate verified OCR output
    manual_records = [
        MultiplierRecord(sequence=1, multiplier=1.25, ocr_confidence=0.95),
        MultiplierRecord(sequence=2, multiplier=2.10, ocr_confidence=0.90),
        MultiplierRecord(sequence=3, multiplier=1.05, ocr_confidence=0.88),
    ]
    updated = await analysis_service.correct_data(
        analysis_id=analysis.id,
        user_id=user_id,
        update_data=MultiplierCorrectionUpdate(records=manual_records),
    )
    assert len(updated.extracted_records) == 3

    # Attempting to analyze before confirmation must raise error
    with pytest.raises(ValueError, match="confirmed by the user"):
        await analysis_service.run_analysis(analysis.id, user_id)

    # 3. Confirm records
    confirmed = await analysis_service.confirm_data(
        analysis_id=analysis.id,
        user_id=user_id,
        confirm_req=MultiplierVerificationConfirm(save_to_historical_dataset=False),
    )
    assert confirmed.extraction_status == "CONFIRMED"
    assert len(confirmed.user_confirmed_records) == 3

    # 4. Run Analysis
    completed = await analysis_service.run_analysis(analysis.id, user_id)
    assert completed.analysis_status == "COMPLETED"
    assert completed.statistics is not None
    assert completed.research_estimate is not None
    # Scientific guardrail: Expect NO_RELIABLE_PREDICTIVE_EDGE_DETECTED when edge not established
    assert completed.research_estimate.verdict in ["NO_RELIABLE_PREDICTIVE_EDGE_DETECTED", "VALIDATED_MODEL_ESTIMATE"]

    # 5. Clean up
    deleted = await analysis_service.delete_analysis(analysis.id, user_id)
    assert deleted is True
