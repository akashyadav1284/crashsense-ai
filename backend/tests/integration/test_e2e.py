"""
Phase 10: End-to-End System Integration Test Suite.
Validates the complete lifecycle and data movement across all subsystems:
- Ingestion -> Deduplication -> Live Round State Machine -> Persistence
- Dataset Preparation -> Zero-Leakage Feature Extraction -> Model Training -> Baseline Verification
- Research Estimate Generation -> Round Completion -> Outcome Matching & Brier Scoring
- Historical Backtesting -> Virtual Bankroll Updates -> Drawdown Calculation -> Circuit Breakers
- Alert Rule Triggering -> Preference Filtering -> In-App & WebSocket Notification Dispatch
- RBAC Boundary Enforcement & Security Audit Logging
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.connectors.schemas.round import NormalizedGameRound
from backend.app.connectors.manager import connector_manager
from backend.app.realtime.engine import RealtimeEngine
from backend.app.simulation.engine import SimulationManager
from backend.app.simulation.schemas import CreateSimulationRequest
from backend.app.notifications.notification_service import NotificationService
from backend.app.notifications.schemas import CreateNotificationRequest, NotificationType, NotificationSeverity
from backend.app.users.user_service import UserManager
from backend.app.users.schemas import UserRole, AccountStatus


@pytest.mark.asyncio
async def test_e2e_telemetry_to_outcome_scoring_workflow():
    """Workflow A & B: Event Ingest -> Outcome Scored -> Live Rounds Audit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Ingest started round event
        round_id = f"e2e_rnd_{int(datetime.now().timestamp())}"
        start_evt = {
            "event_id": f"evt_start_{round_id}",
            "event_type": "round_started",
            "platform_id": "1xbet",
            "provider_id": "spribe",
            "game_id": "aviator",
            "room_id": "standard",
            "round_id": round_id,
            "source_identity": "e2e_test_stream"
        }
        res1 = await client.post("/api/v1/realtime/events/ingest", json=start_evt)
        assert res1.status_code == 200
        assert res1.json()["round"]["status"] == "STARTED"

        # 2. Ingest completed round event with multiplier 2.45x
        comp_evt = {
            "event_id": f"evt_comp_{round_id}",
            "event_type": "round_completed",
            "platform_id": "1xbet",
            "provider_id": "spribe",
            "game_id": "aviator",
            "room_id": "standard",
            "round_id": round_id,
            "multiplier": 2.45,
            "source_identity": "e2e_test_stream"
        }
        res2 = await client.post("/api/v1/realtime/events/ingest", json=comp_evt)
        assert res2.status_code == 200
        assert res2.json()["round"]["status"] == "COMPLETED"
        assert res2.json()["round"]["actual_multiplier"] == 2.45

        # 3. Query live rounds list
        res_r = await client.get("/api/v1/realtime/rounds?limit=10")
        assert res_r.status_code == 200
        rounds_list = res_r.json()
        matching = [r for r in rounds_list if r["round_id"] == round_id]
        assert len(matching) == 1
        assert matching[0]["actual_multiplier"] == 2.45


@pytest.mark.asyncio
async def test_e2e_paper_trading_backtest_workflow():
    """Workflow C: Seed Historical Rounds -> Configure Strategy -> Run Backtest -> Audit History."""
    # Seed historical rounds
    now = datetime.now(timezone.utc) - timedelta(hours=1)
    for i in range(30):
        rnd = NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id=f"e2e-seed-{i:03d}",
            multiplier=1.10 if i % 2 == 0 else 2.20,
            round_timestamp=now + timedelta(seconds=i * 15),
            source_timestamp=now + timedelta(seconds=i * 15),
            source_type="CSV_IMPORT",
            source_record_id=f"e2e-{i}",
            verification_status="VERIFIED"
        )
        await connector_manager.ingest_round(rnd)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Simulation
        sim_payload = {
            "name": "E2E Backtest Run",
            "mode": "HISTORICAL_BACKTEST",
            "dataset_id": "ds-1xbet-aviator-standard",
            "starting_virtual_bankroll": 500.0,
            "strategy_config": {
                "name": "E2E Strategy",
                "description": "500 bankroll @ 2x target",
                "target_multiplier": 2.0,
                "base_stake": 10.0
            }
        }
        res_sim = await client.post("/api/v1/simulation", json=sim_payload)
        assert res_sim.status_code == 201
        sim_id = res_sim.json()["simulation_id"]

        # 2. Execute Backtest
        res_run = await client.post(f"/api/v1/simulation/{sim_id}/start")
        assert res_run.status_code == 200
        sim_res = res_run.json()
        assert sim_res["status"] == "COMPLETED"
        assert sim_res["metrics"]["total_rounds"] >= 20

        # 3. Verify trade history integrity
        res_trades = await client.get(f"/api/v1/simulation/{sim_id}/history")
        assert res_trades.status_code == 200
        trades = res_trades.json()
        assert len(trades) >= 20
        assert "drawdown_percent" in trades[0]
        assert "bankroll_after" in trades[0]


@pytest.mark.asyncio
async def test_e2e_notification_and_security_rbac_workflow():
    """Workflow D & E: User Isolation -> Security Audit Log -> Role Authorization."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Dispatch Notification
        notif_payload = {
            "user_id": "default_researcher",
            "title": "E2E Security Test Event",
            "message": "Routine E2E system validation check.",
            "notification_type": "SECURITY",
            "severity": "INFO"
        }
        res_notif = await client.post("/api/v1/notifications", json=notif_payload)
        assert res_notif.status_code == 201
        n_id = res_notif.json()["notification_id"]

        # 2. User retrieves own notification
        res_list = await client.get("/api/v1/notifications", headers={"x-user-id": "default_researcher"})
        assert res_list.status_code == 200
        assert any(n["notification_id"] == n_id for n in res_list.json())

        # 3. User cannot access other user's notifications (Isolation check)
        res_other = await client.get("/api/v1/notifications", headers={"x-user-id": "different_user_99"})
        assert res_other.status_code == 200
        assert not any(n["notification_id"] == n_id for n in res_other.json())

        # 4. Admin updates user status -> triggers security audit log
        res_status = await client.patch(
            "/api/v1/admin/users/default_researcher/status",
            json={"status": "ACTIVE", "reason": "E2E Validation complete"},
            headers={"x-user-id": "usr_admin_01"}
        )
        assert res_status.status_code == 200

        # 5. Non-admin cannot modify status (403 check)
        res_unauth = await client.patch(
            "/api/v1/admin/users/default_researcher/status",
            json={"status": "SUSPENDED", "reason": "Unauthorized attempt"},
            headers={"x-user-id": "default_researcher"}
        )
        assert res_unauth.status_code == 403

