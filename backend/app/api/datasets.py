"""Datasets API Router."""
import io
import csv
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from backend.app.datasets.models import (
    DatasetMetadata,
    DatasetCreateRequest,
    DatasetValidationReport,
    DatasetCoverageReport,
    PaginatedRoundsResponse,
)
from backend.app.datasets.manager import dataset_manager
from backend.app.datasets.preparation import DataAnalysisPreparation

router = APIRouter(prefix="/datasets", tags=["Historical Datasets & Management"])


@router.get("", response_model=List[DatasetMetadata])
async def list_datasets() -> List[DatasetMetadata]:
    """List isolated historical datasets."""
    return await dataset_manager.list_datasets()


@router.post("", response_model=DatasetMetadata, status_code=status.HTTP_201_CREATED)
async def create_dataset(req: DatasetCreateRequest) -> DatasetMetadata:
    """Create a new isolated dataset partition."""
    existing = await dataset_manager.get_dataset(req.dataset_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset with ID '{req.dataset_id}' already exists."
        )

    return await dataset_manager.create_dataset(
        dataset_id=req.dataset_id,
        platform_id=req.platform_id,
        provider_id=req.provider_id,
        game_id=req.game_id,
        room_id=req.room_id,
        dataset_name=req.dataset_name,
        description=req.description
    )


@router.get("/{dataset_id}", response_model=DatasetMetadata)
async def get_dataset(dataset_id: str) -> DatasetMetadata:
    """Get single dataset metadata."""
    ds = await dataset_manager.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return ds


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: str):
    """Delete a dataset partition metadata."""
    if dataset_id not in dataset_manager._memory_datasets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    del dataset_manager._memory_datasets[dataset_id]
    return None


@router.get("/{dataset_id}/rounds", response_model=PaginatedRoundsResponse)
async def query_dataset_rounds(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None),
    min_multiplier: Optional[float] = Query(None),
    max_multiplier: Optional[float] = Query(None)
) -> PaginatedRoundsResponse:
    """Query paginated rounds within an isolated dataset partition."""
    return await dataset_manager.query_dataset_paginated(
        dataset_id=dataset_id,
        page=page,
        page_size=page_size,
        sort_order=sort,
        search=search,
        min_multiplier=min_multiplier,
        max_multiplier=max_multiplier
    )


@router.get("/{dataset_id}/validation-report", response_model=DatasetValidationReport)
async def get_validation_report(dataset_id: str) -> DatasetValidationReport:
    """Generate comprehensive data quality report for dataset."""
    ds = await dataset_manager.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return await dataset_manager.generate_validation_report(dataset_id)


@router.get("/{dataset_id}/coverage", response_model=DatasetCoverageReport)
async def get_coverage_report(dataset_id: str) -> DatasetCoverageReport:
    """Retrieve coverage period, timestamp continuity, and record spans."""
    ds = await dataset_manager.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found.")
    return await dataset_manager.get_coverage_report(dataset_id)


@router.get("/{dataset_id}/statistics", response_model=Dict[str, Any])
async def get_dataset_statistics(
    dataset_id: str,
    rolling_window: Optional[int] = Query(None, ge=5, le=500)
) -> Dict[str, Any]:
    """Compute empirical moments and optional rolling series."""
    rounds = await dataset_manager.get_dataset_rounds(dataset_id)
    if not rounds:
        return {
            "dataset_id": dataset_id,
            "sample_size": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "variance": None,
            "std_dev": None,
            "rolling_series": []
        }

    mults = [r.multiplier for r in rounds]
    n = len(mults)
    mean_val = sum(mults) / n
    sorted_m = sorted(mults)
    median_val = sorted_m[n // 2] if n % 2 != 0 else (sorted_m[n // 2 - 1] + sorted_m[n // 2]) / 2.0
    var_val = sum((x - mean_val) ** 2 for x in mults) / n if n > 1 else 0.0

    rolling_data = []
    if rolling_window and len(rounds) >= rolling_window:
        rolling_data = DataAnalysisPreparation.extract_rolling_windows(rounds, window_size=rolling_window)

    return {
        "dataset_id": dataset_id,
        "sample_size": n,
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "min": min(mults),
        "max": max(mults),
        "variance": round(var_val, 4),
        "std_dev": round(var_val ** 0.5, 4),
        "rolling_series": rolling_data[:100]
    }


@router.get("/{dataset_id}/export/csv")
async def export_dataset_csv(dataset_id: str):
    """Stream dataset as downloadable CSV."""
    rounds = await dataset_manager.get_dataset_rounds(dataset_id)
    if not rounds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No records to export in this dataset.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "round_id",
        "platform_id",
        "provider_id",
        "game_id",
        "room_id",
        "multiplier",
        "round_timestamp",
        "verification_status",
        "source_type"
    ])
    for r in rounds:
        writer.writerow([
            r.round_id,
            r.platform_id,
            r.provider_id,
            r.game_id,
            r.room_id,
            r.multiplier,
            r.round_timestamp.isoformat(),
            r.verification_status,
            r.source_type
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset_id}.csv"}
    )


@router.get("/{dataset_id}/export/json")
async def export_dataset_json(dataset_id: str):
    """Stream dataset as downloadable JSON."""
    rounds = await dataset_manager.get_dataset_rounds(dataset_id)
    if not rounds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No records to export in this dataset.")

    data = [r.model_dump() for r in rounds]
    json_str = json.dumps(data, default=str, indent=2)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={dataset_id}.json"}
    )
