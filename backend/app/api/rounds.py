"""Rounds & Data Quality API Router."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.schemas.connector import DataQualityEvent
from backend.app.connectors.manager import connector_manager

router = APIRouter(tags=["Rounds & Data Quality"])


@router.get("/rounds", response_model=Dict[str, Any])
async def get_rounds(
    platform: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Query ingested historical rounds with optional filters."""
    rounds = await connector_manager.query_rounds(
        platform_id=platform,
        provider_id=provider,
        limit=limit,
        search=search
    )
    return {
        "total": len(rounds),
        "limit": limit,
        "rounds": [r.model_dump() for r in rounds]
    }


@router.get("/rounds/latest", response_model=Optional[NormalizedGameRound])
async def get_latest_round(platform: Optional[str] = Query(None)) -> Optional[NormalizedGameRound]:
    """Retrieve the single most recent ingested round."""
    rounds = await connector_manager.query_rounds(platform_id=platform, limit=1)
    if not rounds:
        return None
    return rounds[0]


@router.get("/rounds/statistics", response_model=Dict[str, Any])
async def get_rounds_statistics(platform: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Compute empirical statistical moments on actual imported rounds."""
    rounds = await connector_manager.query_rounds(platform_id=platform, limit=5000)
    if not rounds:
        return {
            "sample_size": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "variance": None,
            "std_dev": None,
            "message": "Awaiting ingested historical round data."
        }

    multipliers = [r.multiplier for r in rounds]
    n = len(multipliers)
    mean_val = sum(multipliers) / n
    sorted_m = sorted(multipliers)
    median_val = sorted_m[n // 2] if n % 2 != 0 else (sorted_m[n // 2 - 1] + sorted_m[n // 2]) / 2.0
    var_val = sum((x - mean_val) ** 2 for x in multipliers) / n if n > 1 else 0.0

    return {
        "sample_size": n,
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "min": min(multipliers),
        "max": max(multipliers),
        "variance": round(var_val, 4),
        "std_dev": round(var_val ** 0.5, 4)
    }


@router.get("/data-quality/events", response_model=List[DataQualityEvent])
async def list_data_quality_events(limit: int = Query(50, ge=1, le=200)) -> List[DataQualityEvent]:
    """List data quality anomalies and duplicate events."""
    return await connector_manager.list_dq_events(limit=limit)


@router.get("/data-quality/summary", response_model=Dict[str, Any])
async def get_data_quality_summary() -> Dict[str, Any]:
    """Aggregated data quality report across all sources."""
    events = await connector_manager.list_dq_events(limit=500)
    return {
        "total_anomalies_recorded": len(events),
        "duplicates_detected": sum(1 for e in events if "DUPLICATE" in e.reason),
        "schema_rejections": sum(1 for e in events if "INVALID" in e.reason),
        "recent_events": events[:10]
    }


@router.get("/connectors/status", response_model=Dict[str, Any])
async def get_connectors_status() -> Dict[str, Any]:
    """Diagnostic overview of connector instances."""
    platforms = await connector_manager.list_platforms()
    return {
        "total_platforms": len(platforms),
        "connected_count": sum(1 for p in platforms if p.connection_status == "CONNECTED"),
        "active_instances": list(connector_manager._active_connectors.keys()),
        "supported_adapters": [
            "OFFICIAL_API",
            "LICENSED_FEED",
            "AUTHORIZED_WS",
            "CSV_IMPORT",
            "JSON_IMPORT"
        ]
    }
