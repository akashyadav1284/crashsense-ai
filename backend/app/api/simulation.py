"""
FastAPI Endpoints for Phase 8: Risk Management, Paper Trading & Simulation Engine.
Provides simulation lifecycles (create, start, pause, resume, stop), strategy management,
risk overview, and Monte Carlo scenario analysis.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.simulation.schemas import (
    SimulationRecord,
    SimulationStrategy,
    CreateSimulationRequest,
    MonteCarloRequest,
    MonteCarloResult,
    SimulationPerformanceMetrics,
    SimulatedTrade,
)
from backend.app.simulation.engine import SimulationManager
from backend.app.simulation.monte_carlo import MonteCarloEngine

router = APIRouter(prefix="/simulation", tags=["Paper Trading & Simulation Engine"])
risk_router = APIRouter(prefix="/risk", tags=["Risk Management Engine"])
mc_router = APIRouter(prefix="/monte-carlo", tags=["Monte Carlo Simulation Lab"])

# In-memory store for completed Monte Carlo jobs
_mc_jobs: Dict[str, MonteCarloResult] = {}


# --- 1. Strategy Builder Endpoints (Registered prior to /{simulation_id} to avoid path collision) ---

@router.post("/strategies", response_model=SimulationStrategy, status_code=status.HTTP_201_CREATED)
async def create_strategy(strategy: SimulationStrategy):
    """Create a new research paper strategy."""
    mgr = SimulationManager.get_instance()
    return mgr.create_strategy(strategy)


@router.get("/strategies", response_model=List[SimulationStrategy])
async def list_strategies():
    """List all available research strategies."""
    mgr = SimulationManager.get_instance()
    return mgr.list_strategies()


@router.get("/strategies/{strategy_id}", response_model=SimulationStrategy)
async def get_strategy(strategy_id: str):
    mgr = SimulationManager.get_instance()
    strat = mgr.get_strategy(strategy_id)
    if not strat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Strategy '{strategy_id}' not found.")
    return strat


# --- 2. Simulation Lifecycle Endpoints ---

@router.post("", response_model=SimulationRecord, status_code=status.HTTP_201_CREATED)
async def create_simulation(req: CreateSimulationRequest):
    """Configure a new isolated paper trading simulation."""
    mgr = SimulationManager.get_instance()
    try:
        sim = mgr.create_simulation(req)
        return sim
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[SimulationRecord])
async def list_simulations():
    """List all paper trading simulations."""
    mgr = SimulationManager.get_instance()
    return mgr.list_simulations()


@router.get("/{simulation_id}", response_model=SimulationRecord)
async def get_simulation(simulation_id: str):
    """Retrieve full details of a specific paper simulation."""
    mgr = SimulationManager.get_instance()
    sim = mgr.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Simulation '{simulation_id}' not found.")
    return sim


@router.post("/{simulation_id}/start", response_model=SimulationRecord)
async def start_simulation(simulation_id: str):
    """Start or execute a historical backtest paper simulation."""
    mgr = SimulationManager.get_instance()
    try:
        sim = await mgr.run_historical_backtest(simulation_id)
        return sim
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation failed: {str(e)}")


@router.post("/{simulation_id}/pause", response_model=SimulationRecord)
async def pause_simulation(simulation_id: str):
    mgr = SimulationManager.get_instance()
    sim = mgr.pause_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to pause simulation (must be RUNNING).")
    return sim


@router.post("/{simulation_id}/resume", response_model=SimulationRecord)
async def resume_simulation(simulation_id: str):
    mgr = SimulationManager.get_instance()
    sim = mgr.resume_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resume simulation (must be PAUSED).")
    return sim


@router.post("/{simulation_id}/stop", response_model=SimulationRecord)
async def stop_simulation(simulation_id: str):
    mgr = SimulationManager.get_instance()
    sim = mgr.stop_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Simulation '{simulation_id}' not found.")
    return sim


@router.get("/{simulation_id}/history", response_model=List[SimulatedTrade])
async def get_simulation_history(simulation_id: str):
    """Get trade-by-trade simulated position history."""
    mgr = SimulationManager.get_instance()
    sim = mgr.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Simulation '{simulation_id}' not found.")
    return sim.trades


@router.get("/{simulation_id}/metrics", response_model=SimulationPerformanceMetrics)
async def get_simulation_metrics(simulation_id: str):
    """Get aggregate performance and drawdown metrics for a simulation."""
    mgr = SimulationManager.get_instance()
    sim = mgr.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Simulation '{simulation_id}' not found.")
    return sim.metrics


# --- 3. Risk Management Endpoints ---

@risk_router.get("/overview")
async def get_risk_overview():
    """Aggregate risk statistics across all simulations."""
    mgr = SimulationManager.get_instance()
    sims = mgr.list_simulations()

    total_sims = len(sims)
    total_trades = sum(len(s.trades) for s in sims)
    total_breaches = sum(len(s.metrics.risk_limit_breaches) for s in sims)

    # Max drawdown across all simulations
    max_observed_dd = max([s.metrics.max_drawdown_percent for s in sims], default=0.0)

    return {
        "total_simulations": total_sims,
        "total_simulated_positions": total_trades,
        "total_risk_limit_breaches": total_breaches,
        "max_observed_drawdown_percent": max_observed_dd,
        "simulations": [
            {
                "simulation_id": s.simulation_id,
                "name": s.name,
                "status": s.status.value,
                "net_pnl": s.metrics.net_pnl,
                "return_percentage": s.metrics.return_percentage,
                "max_drawdown": s.metrics.max_drawdown_percent,
                "breaches": s.metrics.risk_limit_breaches,
            }
            for s in sims
        ]
    }


# --- 4. Monte Carlo Risk Analysis Endpoints ---

@mc_router.post("/run", response_model=MonteCarloResult, status_code=status.HTTP_201_CREATED)
async def run_monte_carlo(req: MonteCarloRequest):
    """Run hypothetical Monte Carlo bankroll trajectory analysis."""
    try:
        result = MonteCarloEngine.run_simulation(req)
        _mc_jobs[result.job_id] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Monte Carlo execution failed: {str(e)}")


@mc_router.get("/jobs", response_model=List[MonteCarloResult])
async def list_monte_carlo_jobs():
    """List completed Monte Carlo analysis runs."""
    return sorted(list(_mc_jobs.values()), key=lambda x: x.executed_at, reverse=True)


@mc_router.get("/{job_id}", response_model=MonteCarloResult)
async def get_monte_carlo_job(job_id: str):
    """Retrieve full results of a specific Monte Carlo job."""
    res = _mc_jobs.get(job_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monte Carlo job '{job_id}' not found.")
    return res
