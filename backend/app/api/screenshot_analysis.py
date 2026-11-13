"""FastAPI endpoints for screenshot-based Aviator analysis."""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status

from backend.app.screenshot_analysis.schemas import (
    ScreenshotAnalysisResponse,
    MultiplierCorrectionUpdate,
    MultiplierVerificationConfirm,
)
from backend.app.screenshot_analysis.analysis_service import analysis_service

router = APIRouter(prefix="/screenshot-analysis", tags=["Screenshot Analysis"])

# Simple user resolver (consistent with existing Phase 8/9 mocked session / token dependency)
async def get_current_user_id() -> str:
    """Returns current active user identifier."""
    return "usr_demo_trader"


@router.post("/upload", response_model=ScreenshotAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_screenshot(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Uploads a screenshot of Spribe Aviator multiplier history and triggers OCR parsing."""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media type {file.content_type}. Allowed: PNG, JPEG, JPG, WEBP",
        )

    file_bytes = await file.read()
    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowable limit of 15MB.",
        )

    try:
        res = await analysis_service.create_analysis(
            user_id=user_id,
            filename=file.filename or "aviator_screenshot.png",
            content_type=file.content_type,
            file_bytes=file_bytes,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/{analysis_id}/extract", response_model=ScreenshotAnalysisResponse)
async def trigger_extraction(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Re-triggers extraction or checks status."""
    analysis = await analysis_service.get_analysis(analysis_id, user_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


@router.get("/{analysis_id}/extracted-data", response_model=ScreenshotAnalysisResponse)
async def get_extracted_data(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieves extracted OCR records."""
    analysis = await analysis_service.get_analysis(analysis_id, user_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


@router.put("/{analysis_id}/correct-data", response_model=ScreenshotAnalysisResponse)
async def correct_data(
    analysis_id: str,
    update_data: MultiplierCorrectionUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Applies user manual edits, additions, deletions, or sequence reorderings."""
    try:
        return await analysis_service.correct_data(analysis_id, user_id, update_data)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))


@router.post("/{analysis_id}/confirm", response_model=ScreenshotAnalysisResponse)
async def confirm_data(
    analysis_id: str,
    confirm_req: MultiplierVerificationConfirm,
    user_id: str = Depends(get_current_user_id),
):
    """Confirms extracted multipliers and unlocks statistical / ML analysis."""
    try:
        return await analysis_service.confirm_data(analysis_id, user_id, confirm_req)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/{analysis_id}/analyze", response_model=ScreenshotAnalysisResponse)
async def run_analysis(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Runs statistical calculations and ML research estimation."""
    try:
        return await analysis_service.run_analysis(analysis_id, user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/{analysis_id}/result", response_model=ScreenshotAnalysisResponse)
async def get_analysis_result(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Retrieves analysis results including statistical distributions and research estimates."""
    analysis = await analysis_service.get_analysis(analysis_id, user_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


@router.get("/history", response_model=List[ScreenshotAnalysisResponse])
async def list_history(
    user_id: str = Depends(get_current_user_id),
):
    """Lists past screenshot analyses for the authenticated user."""
    return await analysis_service.list_history(user_id)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Deletes an analysis session and associated stored image."""
    success = await analysis_service.delete_analysis(analysis_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return None
