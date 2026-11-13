"""Historical Data Import API Router (CSV & JSON)."""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from backend.app.connectors.adapters.csv_import import CSVImportAdapter
from backend.app.connectors.adapters.json_import import JSONImportAdapter
from backend.app.connectors.schemas.connector import ImportJob
from backend.app.connectors.manager import connector_manager

router = APIRouter(prefix="/import", tags=["Data Ingestion & Historical Import"])


@router.post("/csv", response_model=ImportJob)
async def import_csv_file(
    file: UploadFile = File(...),
    platform_id: str = Form(default="csv_import"),
    provider_id: str = Form(default="generic"),
    game_id: str = Form(default="crash"),
    room_id: str = Form(default="standard")
) -> ImportJob:
    """Upload and ingest a historical multiplier CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid .csv file"
        )

    content_bytes = await file.read()
    csv_text = content_bytes.decode("utf-8", errors="replace")

    job_id = f"job-csv-{uuid.uuid4().hex[:8]}"
    adapter = CSVImportAdapter(
        connector_id="csv_parser",
        configuration={
            "default_platform": platform_id,
            "default_provider": provider_id,
            "default_game": game_id,
            "default_room": room_id
        }
    )

    try:
        raw_rows = adapter.parse_csv_content(csv_text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV parsing error: {str(exc)}"
        )

    # Convert to NormalizedGameRound
    normalized_records = []
    rejection_errors = []
    for row in raw_rows:
        try:
            norm = adapter.normalize_record(row)
            normalized_records.append(norm)
        except Exception as exc:
            rejection_errors.append(str(exc))

    job = ImportJob(
        job_id=job_id,
        source_id=platform_id,
        source_type="CSV_IMPORT",
        total_records=len(raw_rows),
        rejected_records=len(rejection_errors),
        errors=rejection_errors[:20]
    )
    connector_manager._memory_import_jobs[job_id] = job

    # Execute batch ingestion
    completed_job = await connector_manager.ingest_batch(job_id, normalized_records)
    return completed_job


@router.post("/json", response_model=ImportJob)
async def import_json_file(
    file: UploadFile = File(...),
    platform_id: str = Form(default="json_import"),
    provider_id: str = Form(default="generic"),
    game_id: str = Form(default="crash"),
    room_id: str = Form(default="standard")
) -> ImportJob:
    """Upload and ingest historical multiplier JSON / NDJSON file."""
    content_bytes = await file.read()
    json_text = content_bytes.decode("utf-8", errors="replace")

    job_id = f"job-json-{uuid.uuid4().hex[:8]}"
    adapter = JSONImportAdapter(
        connector_id="json_parser",
        configuration={
            "default_platform": platform_id,
            "default_provider": provider_id,
            "default_game": game_id,
            "default_room": room_id
        }
    )

    try:
        raw_items = adapter.parse_json_content(json_text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"JSON parsing error: {str(exc)}"
        )

    normalized_records = []
    rejection_errors = []
    for item in raw_items:
        try:
            norm = adapter.normalize_record(item)
            normalized_records.append(norm)
        except Exception as exc:
            rejection_errors.append(str(exc))

    job = ImportJob(
        job_id=job_id,
        source_id=platform_id,
        source_type="JSON_IMPORT",
        total_records=len(raw_items),
        rejected_records=len(rejection_errors),
        errors=rejection_errors[:20]
    )
    connector_manager._memory_import_jobs[job_id] = job

    completed_job = await connector_manager.ingest_batch(job_id, normalized_records)
    return completed_job


@router.get("/jobs", response_model=List[ImportJob])
async def list_import_jobs() -> List[ImportJob]:
    """List historical file import jobs."""
    return list(connector_manager._memory_import_jobs.values())


@router.get("/jobs/{job_id}", response_model=ImportJob)
async def get_import_job(job_id: str) -> ImportJob:
    """Get single import job details."""
    job = connector_manager._memory_import_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=ImportJob)
async def cancel_import_job(job_id: str) -> ImportJob:
    """Cancel an active or queued import job."""
    job = connector_manager._memory_import_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    if job.status == "PROCESSING":
        job.status = "CANCELLED"
    return job
