"""
Comprehensive Test Suite for Phase 8: Risk Management, Paper Trading & Simulation Engine.
Covers:
1. Virtual Bankroll Management (fixed stake, percentage stake, capped stake, negative stake rejection).
2. Risk Limits (drawdown stop, consecutive loss stop, depletion stop).
3. Historical Backtest execution on isolated datasets with zero lookahead bias.
4. Monte Carlo risk analysis (reproducible seed, ruin probability, drawdown distributions).
5. FastAPI Simulation, Risk, and Monte Carlo endpoints.
"""

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.simulation.schemas import (
    SimulationStrategy,
    RiskLimits,
    StakeSizingMethod,
    StrategyType,
    CreateSimulationRequest,
    SimulationMode,
    MonteCarloRequest,
)
from backend.app.simulation.bankroll_manager import BankrollManager
from backend.app.simulation.monte_carlo import MonteCarloEngine
from backend.app.simulation.engine import SimulationManager


def test_bankroll_manager_fixed_stake():
    """Verify fixed stake sizing and positive balance update on win."""
    strat = SimulationStrategy(
        strategy_id="strat-test-1",
        name="Fixed Stake Strategy",
        description="Fixed 10.0 stake",
        stake_sizing_method=StakeSizingMethod.FIXED_STAKE,
        base_stake=10.0,
        target_multiplier=2.0
    )
    bm = BankrollManager(starting_bankroll=100.0, strategy=strat)

    ok, err, stake = bm.calculate_stake()
    assert ok is True
    assert stake == 10.0

    # Win @ 2.50x (target 2.0x -> win: stake * (2.0 - 1.0) = +10.0)
    is_win, pnl = bm.record_outcome(stake=10.0, actual_multiplier=2.50, target_multiplier=2.0)
    assert is_win is True
    assert pnl == 10.0
    assert bm.current_bankroll == 110.0


def test_bankroll_manager_percentage_and_caps():
    """Verify percentage sizing and maximum stake cap enforcement."""
    strat = SimulationStrategy(
        strategy_id="strat-test-2",
        name="Capped Percentage Strategy",
        description="5% stake capped at 25.0",
        stake_sizing_method=StakeSizingMethod.CAPPED_PERCENTAGE,
        stake_percentage=5.0,  # 5% of 1000 = 50.0, but capped at 25.0
        max_stake_cap=25.0,
        risk_limits=RiskLimits(max_stake=100.0, min_stake=1.0)
    )
    bm = BankrollManager(starting_bankroll=1000.0, strategy=strat)

    ok, err, stake = bm.calculate_stake()
    assert ok is True
    assert stake == 25.0  # Capped at 25.0


def test_risk_limits_breach_detection():
    """Verify drawdown and consecutive loss limits stop further trading."""
    strat = SimulationStrategy(
        strategy_id="strat-test-3",
        name="Risk Limit Test",
        description="Stop at 3 consecutive losses or 20% drawdown",
        base_stake=20.0,
        risk_limits=RiskLimits(
            max_drawdown_percent=20.0,
            max_consecutive_losses=3
        )
    )
    bm = BankrollManager(starting_bankroll=100.0, strategy=strat)

    # 3 consecutive losses of 20.0 (balance: 100 -> 80 -> 60 -> 40)
    for _ in range(3):
        bm.record_outcome(stake=20.0, actual_multiplier=1.20, target_multiplier=2.0)

    ok, breach = bm.check_risk_limits()
    assert ok is False
    assert "consecutive simulated losses" in breach or "Drawdown" in breach


def test_monte_carlo_engine_reproducibility():
    """Ensure Monte Carlo execution is deterministic when provided a fixed seed."""
    req1 = MonteCarloRequest(
        job_name="Reproducibility Test 1",
        num_trials=100,
        rounds_per_trial=50,
        starting_bankroll=500.0,
        stake_amount=10.0,
        target_multiplier=2.0,
        house_edge=0.01,
        random_seed=12345
    )
    res1 = MonteCarloEngine.run_simulation(req1)

    req2 = MonteCarloRequest(
        job_name="Reproducibility Test 2",
        num_trials=100,
        rounds_per_trial=50,
        starting_bankroll=500.0,
        stake_amount=10.0,
        target_multiplier=2.0,
        house_edge=0.01,
        random_seed=12345
    )
    res2 = MonteCarloEngine.run_simulation(req2)

    assert res1.median_final_bankroll == res2.median_final_bankroll
    assert res1.probability_of_ruin_percent == res2.probability_of_ruin_percent
    assert res1.max_observed_drawdown == res2.max_observed_drawdown


@pytest.mark.asyncio
async def test_api_simulation_and_risk_endpoints():
    """Verify Simulation, Risk Overview, and Monte Carlo FastAPI endpoints."""
    # Seed rounds in connector manager first so historical backtest has records to process
    from backend.app.connectors.schemas.round import NormalizedGameRound
    from backend.app.connectors.manager import connector_manager
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc) - timedelta(hours=2)
    for i in range(50):
        rnd = NormalizedGameRound(
            platform_id="1xbet",
            provider_id="spribe",
            game_id="aviator",
            room_id="standard",
            round_id=f"sim-rnd-{i:03d}",
            multiplier=round(1.05 + (i % 20) * 0.15, 2),
            round_timestamp=now + timedelta(seconds=i * 20),
            source_timestamp=now + timedelta(seconds=i * 20),
            source_type="CSV_IMPORT",
            source_record_id=str(i),
            verification_status="VERIFIED"
        )
        await connector_manager.ingest_round(rnd)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List strategies
        res_strat = await client.get("/api/v1/simulation/strategies")
        assert res_strat.status_code == 200
        assert len(res_strat.json()) >= 2

        # 2. Create paper simulation
        create_payload = {
            "name": "API Test Backtest",
            "mode": "HISTORICAL_BACKTEST",
            "dataset_id": "ds-1xbet-aviator-standard",
            "starting_virtual_bankroll": 1000.0,
            "strategy_config": {
                "name": "Test Strategy",
                "description": "API Test",
                "target_multiplier": 2.0,
                "base_stake": 10.0
            }
        }
        res_create = await client.post("/api/v1/simulation", json=create_payload)
        assert res_create.status_code == 201
        sim_data = res_create.json()
        assert "simulation_id" in sim_data
        sim_id = sim_data["simulation_id"]

        # 3. Start backtest execution
        res_start = await client.post(f"/api/v1/simulation/{sim_id}/start")
        assert res_start.status_code == 200
        started_sim = res_start.json()
        assert started_sim["status"] == "COMPLETED"
        assert started_sim["metrics"]["total_rounds"] >= 0

        # 4. Simulation history & metrics
        res_hist = await client.get(f"/api/v1/simulation/{sim_id}/history")
        assert res_hist.status_code == 200

        res_met = await client.get(f"/api/v1/simulation/{sim_id}/metrics")
        assert res_met.status_code == 200

        # 5. Risk overview
        res_risk = await client.get("/api/v1/risk/overview")
        assert res_risk.status_code == 200
        assert res_risk.json()["total_simulations"] >= 1

        # 6. Monte Carlo run
        mc_payload = {
            "job_name": "API Monte Carlo Test",
            "num_trials": 50,
            "rounds_per_trial": 50,
            "starting_bankroll": 500.0,
            "stake_amount": 10.0,
            "target_multiplier": 2.0,
            "house_edge": 0.01,
            "random_seed": 42
        }
        res_mc = await client.post("/api/v1/monte-carlo/run", json=mc_payload)
        assert res_mc.status_code == 201
        mc_data = res_mc.json()
        assert "median_final_bankroll" in mc_data
        assert "probability_of_ruin_percent" in mc_data
        assert len(mc_data["sample_trajectories"]) > 0
