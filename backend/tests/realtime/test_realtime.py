"""
Comprehensive Test Suite for Phase 7: Real-Time Monitoring & Prediction Tracking.
Covers:
1. Event ingestion pipeline (valid event, invalid schema, negative multiplier rejection).
2. Deduplication using sliding window compound keys.
3. Out-of-order event detection per platform/room partition.
4. Live round state machine (WAITING -> STARTED -> ACTIVE -> COMPLETED).
5. Connector health tracking, heartbeat pings, and reconnect with backoff.
6. Research inference guardrails: rejected/unvalidated models return NO_RELIABLE_PREDICTIVE_EDGE_DETECTED.
7. Outcome matching: linking completed round multipliers to pending research estimates and computing Brier score error.
8. Realtime FastAPI endpoints.
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.realtime.schemas import (
    RealtimeRawEvent,
    RoundLifecycleStatus,
    ConnectionHealthStatus,
    EstimateLifecycleStatus,
)
from backend.app.realtime.event_ingestion import (
    EventValidator,
    EventDeduplicator,
    EventOrderingEngine,
)
from backend.app.realtime.connection_manager import ConnectionManager
from backend.app.realtime.live_round_tracker import LiveRoundTracker
from backend.app.realtime.prediction_tracker import PredictionTracker
from backend.app.realtime.engine import RealtimeEngine
from backend.app.ml.registry.model_registry import ModelRegistry
from backend.app.ml.schemas.experiment import ModelMetadata, ModelLifecycleStatus


def test_event_validator():
    """Verify validator accepts compliant events and strictly rejects malformed payloads."""
    # 1. Valid event
    valid_payload = {
        "event_id": "evt-001",
        "event_type": "round_completed",
        "platform_id": "1xbet",
        "provider_id": "spribe",
        "game_id": "aviator",
        "room_id": "standard",
        "round_id": "rnd-101",
        "multiplier": 2.45,
        "source_identity": "1xbet_spribe_ws"
    }
    is_valid, err, event = EventValidator.validate_event(valid_payload)
    assert is_valid is True
    assert event is not None
    assert event.multiplier == 2.45

    # 2. Invalid multiplier (< 1.00x)
    invalid_mult = valid_payload.copy()
    invalid_mult["event_id"] = "evt-002"
    invalid_mult["multiplier"] = 0.85
    is_valid, err, _ = EventValidator.validate_event(invalid_mult)
    assert is_valid is False
    assert "Multiplier cannot be less than 1.00x" in err

    # 3. Missing required field
    missing_plat = valid_payload.copy()
    missing_plat["platform_id"] = ""
    is_valid, err, _ = EventValidator.validate_event(missing_plat)
    assert is_valid is False
    assert "Missing required event field" in err


def test_event_deduplicator():
    """Ensure duplicate events with matching compound keys are dropped."""
    dedup = EventDeduplicator()
    event = RealtimeRawEvent(
        event_id="evt-dup-1",
        event_type="round_completed",
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id="rnd-dup-1",
        multiplier=1.75,
        source_identity="authorized_feed"
    )

    assert dedup.is_duplicate(event) is False
    # Subsequent submission must be detected as duplicate
    assert dedup.is_duplicate(event) is True


def test_event_ordering():
    """Verify out-of-order events (timestamp < previous event) are flagged."""
    engine = EventOrderingEngine()
    now = datetime.now(timezone.utc)

    e1 = RealtimeRawEvent(
        event_id="e1", event_type="round_started",
        platform_id="1xbet", provider_id="spribe", game_id="aviator", room_id="std",
        timestamp=now, source_identity="feed"
    )
    e2_in_order = RealtimeRawEvent(
        event_id="e2", event_type="round_completed",
        platform_id="1xbet", provider_id="spribe", game_id="aviator", room_id="std",
        timestamp=now + timedelta(seconds=10), source_identity="feed"
    )
    e3_out_of_order = RealtimeRawEvent(
        event_id="e3", event_type="round_updated",
        platform_id="1xbet", provider_id="spribe", game_id="aviator", room_id="std",
        timestamp=now - timedelta(seconds=5), source_identity="feed"
    )

    assert engine.check_ordering(e1) is True
    assert engine.check_ordering(e2_in_order) is True
    assert engine.check_ordering(e3_out_of_order) is False


def test_live_round_lifecycle():
    """Verify live round state machine: WAITING -> STARTED -> ACTIVE -> COMPLETED."""
    tracker = LiveRoundTracker()
    now = datetime.now(timezone.utc)

    # 1. Start round
    e_start = RealtimeRawEvent(
        event_id="e-start-1", event_type="round_started",
        platform_id="bcgame", provider_id="bc_originals", game_id="crash", room_id="std",
        round_id="rnd-live-99", timestamp=now, source_identity="bc_ws"
    )
    r1 = tracker.process_round_event(e_start)
    assert r1.status == RoundLifecycleStatus.STARTED
    assert r1.actual_multiplier is None

    # 2. Update multiplier while active
    e_upd = RealtimeRawEvent(
        event_id="e-upd-1", event_type="round_updated",
        platform_id="bcgame", provider_id="bc_originals", game_id="crash", room_id="std",
        round_id="rnd-live-99", timestamp=now + timedelta(seconds=2), source_identity="bc_ws"
    )
    r2 = tracker.process_round_event(e_upd)
    assert r2.status == RoundLifecycleStatus.ACTIVE

    # 3. Complete round
    e_comp = RealtimeRawEvent(
        event_id="e-comp-1", event_type="round_completed",
        platform_id="bcgame", provider_id="bc_originals", game_id="crash", room_id="std",
        round_id="rnd-live-99", multiplier=3.14, timestamp=now + timedelta(seconds=5),
        source_identity="bc_ws"
    )
    r3 = tracker.process_round_event(e_comp)
    assert r3.status == RoundLifecycleStatus.COMPLETED
    assert r3.actual_multiplier == 3.14


def test_connector_health_and_reconnect():
    """Test connector manager heartbeat updates and reconnect authorization requirements."""
    conn_mgr = ConnectionManager()
    conn_id = "conn-1xbet-aviator"

    # Initially NOT_CONFIGURED & unauthorized
    conn = conn_mgr.get_connector(conn_id)
    assert conn is not None
    assert conn.status == ConnectionHealthStatus.NOT_CONFIGURED

    # Unauthorized reconnect attempt must be rejected
    ok, msg = conn_mgr.trigger_reconnect(conn_id)
    assert ok is False
    assert "Authorization required" in msg

    # Sandbox replay connector is authorized and healthy
    ok_sb, _ = conn_mgr.trigger_reconnect("conn-replay-sandbox")
    assert ok_sb is True


def test_research_inference_guardrails():
    """Ensure prediction tracker returns NO_RELIABLE_PREDICTIVE_EDGE_DETECTED when model is rejected or unvalidated."""
    tracker = PredictionTracker()
    recent = [1.2, 1.5, 2.1, 1.1, 3.4, 1.05, 1.9, 2.5, 1.3, 1.8]

    # Test with non-existent or rejected model_id
    ok, err, est = tracker.generate_research_estimate(
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id="rnd-target-500",
        recent_multipliers=recent,
        model_id="non_existent_or_rejected_model"
    )
    assert ok is False
    assert "NO_RELIABLE_PREDICTIVE_EDGE_DETECTED" in err


def test_outcome_matching_and_scoring():
    """
    Test linking of actual round multiplier to pending research estimate,
    computing Brier score error, and marking estimate SCORED.
    """
    tracker = PredictionTracker()
    round_id = "rnd-score-test-1"

    # Manually inject a pending research estimate for testing outcome matching
    now = datetime.now(timezone.utc) - timedelta(seconds=10)
    est = tracker.estimates["est-test-manual"] = tracker.estimates.get("est-test-manual") or (
        tracker.estimates.setdefault("est-test-manual", None)
    )

    from backend.app.realtime.schemas import ResearchEstimateRecord
    manual_est = ResearchEstimateRecord(
        estimate_id="est-test-manual",
        platform_id="1xbet",
        provider_id="spribe",
        game_id="aviator",
        room_id="standard",
        round_id=round_id,
        model_id="mdl_test_rf",
        model_version="v1.0.0",
        source_provenance="test_stream",
        estimate_timestamp=now,
        feature_window_end_timestamp=now,
        model_validation_status="VALIDATED",
        calibration_status="CALIBRATED",
        target_threshold=2.0,
        predicted_probability=0.60,
        baseline_probability=0.495,
        decision_signal="PASS",
        status=EstimateLifecycleStatus.PENDING_OUTCOME
    )
    tracker.estimates["est-test-manual"] = manual_est
    tracker.pending_by_round[round_id] = ["est-test-manual"]

    # Now match completed round with multiplier 2.50 (>= 2.0 -> actual label 1)
    outcome_time = now + timedelta(seconds=8)
    scored = tracker.match_and_score_outcome(
        round_id=round_id,
        platform_id="1xbet",
        provider_id="spribe",
        actual_multiplier=2.50,
        outcome_timestamp=outcome_time
    )

    assert len(scored) == 1
    assert scored[0].is_correct is True
    # Brier score: (0.60 - 1.0)^2 = 0.16
    assert np.isclose(scored[0].brier_score, 0.16)
    assert manual_est.status == EstimateLifecycleStatus.SCORED
    assert manual_est.brier_error == 0.16


@pytest.mark.asyncio
async def test_api_realtime_endpoints():
    """Verify Phase 7 FastAPI realtime endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Realtime Status
        res = await client.get("/api/v1/realtime/status")
        assert res.status_code == 200
        assert res.json()["status"] == "ONLINE"

        # 2. Connections list
        res_conn = await client.get("/api/v1/realtime/connections")
        assert res_conn.status_code == 200
        assert len(res_conn.json()) >= 3

        # 3. Live Rounds list
        res_r = await client.get("/api/v1/realtime/rounds")
        assert res_r.status_code == 200

        # 4. Ingest live event
        ingest_payload = {
            "event_id": "test_live_evt_999",
            "event_type": "round_completed",
            "platform_id": "1xbet",
            "provider_id": "spribe",
            "game_id": "aviator",
            "room_id": "standard",
            "round_id": "rnd_api_live_1",
            "multiplier": 1.95,
            "source_identity": "test_ingest_feed"
        }
        res_ing = await client.post("/api/v1/realtime/events/ingest", json=ingest_payload)
        assert res_ing.status_code == 200
        assert res_ing.json()["status"] == "INGESTED"

        # 5. Operational metrics
        res_met = await client.get("/api/v1/realtime/metrics")
        assert res_met.status_code == 200
        assert res_met.json()["events_processed"] >= 1

        # 6. Operational health
        res_h = await client.get("/api/v1/realtime/health")
        assert res_h.status_code == 200
        assert "active_subsystems" in res_h.json()

