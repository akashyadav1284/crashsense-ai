"""
FastAPI Endpoints for Phase 7: Real-Time Monitoring & Prediction Tracking.
Handles live connection status, real-time event ingestion, live rounds,
research estimates, outcome tracking, evaluations, and operational metrics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.realtime.schemas import (
    LiveRoundRecord,
    ConnectorHealthStatus,
    ResearchEstimateRecord,
    ScoredOutcomeRecord,
    OperationalMetrics,
    EstimateEvaluationSummary,
    EstimateLifecycleStatus,
)
from backend.app.realtime.engine import RealtimeEngine
from backend.app.realtime.connection_manager import ConnectionManager
from backend.app.realtime.live_round_tracker import LiveRoundTracker
from backend.app.realtime.prediction_tracker import PredictionTracker

router = APIRouter(prefix="/realtime", tags=["Real-Time Monitoring & Prediction Tracking"])


class RunEstimateRequest(BaseModel):
    platform_id: str = "1xbet"
    provider_id: str = "spribe"
    game_id: str = "aviator"
    room_id: str = "standard"
    round_id: Optional[str] = None
    model_id: Optional[str] = None
    target_threshold: float = 2.0
    recent_multipliers: List[float] = Field(..., min_length=10)


class IngestEventRequest(BaseModel):
    event_id: str
    event_type: str
    platform_id: str
    provider_id: str
    game_id: str
    room_id: str
    round_id: Optional[str] = None
    multiplier: Optional[float] = None
    source_identity: str
    payload: Dict[str, Any] = Field(default_factory=dict)


# --- 1. Live Monitoring & Connections ---

@router.get("/status")
async def get_realtime_status():
    """Overall status of real-time monitoring subsystems."""
    engine = RealtimeEngine.get_instance()
    metrics = engine.get_operational_metrics()
    return {
        "status": "ONLINE",
        "active_connectors": metrics.active_connectors,
        "events_processed": metrics.events_processed,
        "websocket_clients": metrics.websocket_client_count,
        "avg_latency_ms": metrics.average_processing_latency_ms,
        "last_event": metrics.last_event_timestamp,
    }


@router.get("/connections", response_model=List[ConnectorHealthStatus])
async def list_connections():
    """List operational states and heartbeat times for all platform feeds."""
    conn_mgr = ConnectionManager.get_instance()
    return conn_mgr.list_connectors()


@router.post("/connections/{connector_id}/reconnect")
async def reconnect_connector(connector_id: str):
    """Trigger reconnection with backoff on a supported connector."""
    conn_mgr = ConnectionManager.get_instance()
    ok, msg = conn_mgr.trigger_reconnect(connector_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"connector_id": connector_id, "status": "RECONNECTED", "message": msg}


# --- 2. Live Rounds & Events Ingest ---

@router.post("/events/ingest")
async def ingest_event(req: IngestEventRequest):
    """Ingest a validated live event into the real-time processing pipeline."""
    engine = RealtimeEngine.get_instance()
    ok, msg, round_rec = await engine.ingest_event(req.dict())
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "INGESTED", "message": msg, "round": round_rec}


@router.get("/rounds", response_model=List[LiveRoundRecord])
async def list_live_rounds(
    platform_id: Optional[str] = Query(None),
    provider_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List active and recently completed live crash rounds."""
    tracker = LiveRoundTracker.get_instance()
    return tracker.list_live_rounds(platform_id=platform_id, provider_id=provider_id, limit=limit)


@router.get("/rounds/{round_id}", response_model=LiveRoundRecord)
async def get_live_round(round_id: str):
    """Query a specific round by round ID."""
    tracker = LiveRoundTracker.get_instance()
    rnd = tracker.get_round(round_id)
    if not rnd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Round '{round_id}' not found.")
    return rnd


# --- 3. Research Estimates ---

@router.get("/estimates", response_model=List[ResearchEstimateRecord])
async def list_estimates(status: Optional[EstimateLifecycleStatus] = Query(None)):
    """List generated research estimates filtered by lifecycle status."""
    tracker = PredictionTracker.get_instance()
    return tracker.list_estimates(status=status)


@router.get("/estimates/{estimate_id}", response_model=ResearchEstimateRecord)
async def get_estimate(estimate_id: str):
    """Retrieve detailed research estimate record."""
    tracker = PredictionTracker.get_instance()
    est = tracker.get_estimate(estimate_id)
    if not est:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Estimate '{estimate_id}' not found.")
    return est


@router.post("/estimates/run", response_model=ResearchEstimateRecord, status_code=status.HTTP_201_CREATED)
async def run_research_estimate(req: RunEstimateRequest):
    """
    Generate a guarded research estimate using an active, validated model.
    Returns NO_RELIABLE_PREDICTIVE_EDGE_DETECTED if model is not validated or has no edge.
    """
    tracker = PredictionTracker.get_instance()
    ok, err_msg, record = tracker.generate_research_estimate(
        platform_id=req.platform_id,
        provider_id=req.provider_id,
        game_id=req.game_id,
        room_id=req.room_id,
        round_id=req.round_id,
        recent_multipliers=req.recent_multipliers,
        model_id=req.model_id,
        target_threshold=req.target_threshold,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    return record


@router.get("/estimates/summary", response_model=EstimateEvaluationSummary)
async def get_estimates_summary():
    """Retrieve aggregate performance and Brier score evaluation across all scored estimates."""
    tracker = PredictionTracker.get_instance()
    return tracker.get_evaluations_summary()


# --- 4. Outcomes & Evaluations ---

@router.get("/outcomes", response_model=List[ScoredOutcomeRecord])
async def list_scored_outcomes(limit: int = Query(50, ge=1, le=200)):
    """List audit log of scored round outcomes matched to research estimates."""
    tracker = PredictionTracker.get_instance()
    return tracker.list_scored_outcomes(limit=limit)


@router.get("/evaluations/summary", response_model=EstimateEvaluationSummary)
async def get_evaluations_summary():
    """Detailed evaluation summary comparing predictions vs theoretical null baseline."""
    tracker = PredictionTracker.get_instance()
    return tracker.get_evaluations_summary()


# --- 5. Operational Health & Metrics ---

@router.get("/health")
async def get_realtime_health():
    """Health classification for operational monitoring pipeline."""
    engine = RealtimeEngine.get_instance()
    conn_mgr = ConnectionManager.get_instance()
    metrics = engine.get_operational_metrics()

    connectors = conn_mgr.list_connectors()
    healthy = [c for c in connectors if c.status == "HEALTHY"]

    return {
        "status": "HEALTHY" if healthy else "DEGRADED",
        "active_subsystems": ["ingestion", "deduplicator", "ordering", "prediction_tracker", "websocket_hub"],
        "healthy_connectors": len(healthy),
        "total_connectors": len(connectors),
        "events_processed": metrics.events_processed,
        "processing_latency_ms": metrics.average_processing_latency_ms,
    }


@router.get("/metrics", response_model=OperationalMetrics)
async def get_operational_metrics():
    """Detailed operational metrics."""
    engine = RealtimeEngine.get_instance()
    return engine.get_operational_metrics()

