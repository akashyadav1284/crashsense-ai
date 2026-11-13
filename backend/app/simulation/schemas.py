"""
Pydantic Schemas and Data Contracts for Phase 8: Risk Management, Paper Trading & Simulation Engine.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class SimulationMode(str, Enum):
    HISTORICAL_BACKTEST = "HISTORICAL_BACKTEST"
    REPLAY_SIMULATION = "REPLAY_SIMULATION"
    LIVE_PAPER = "LIVE_PAPER"


class SimulationStatus(str, Enum):
    CREATED = "CREATED"
    CONFIGURED = "CONFIGURED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class StakeSizingMethod(str, Enum):
    FIXED_STAKE = "FIXED_STAKE"
    PERCENTAGE_OF_BANKROLL = "PERCENTAGE_OF_BANKROLL"
    CAPPED_PERCENTAGE = "CAPPED_PERCENTAGE"
    CUSTOM_RULE = "CUSTOM_RULE"


class StrategyType(str, Enum):
    FIXED_STAKE = "FIXED_STAKE"
    FIXED_PERCENTAGE = "FIXED_PERCENTAGE"
    HISTORICAL_THRESHOLD = "HISTORICAL_THRESHOLD"
    MOVING_WINDOW_STATISTICAL = "MOVING_WINDOW_STATISTICAL"
    RESEARCH_MODEL_ASSISTED = "RESEARCH_MODEL_ASSISTED"
    CUSTOM_RULE_BASED = "CUSTOM_RULE_BASED"


class RiskLimits(BaseModel):
    max_stake: float = 100.0
    min_stake: float = 1.0
    max_daily_loss: float = 500.0
    max_drawdown_percent: float = 25.0
    max_consecutive_losses: int = 5
    max_simulated_rounds: int = 500
    stop_on_depletion: bool = True
    stop_on_limit_breach: bool = True


class SimulationStrategy(BaseModel):
    strategy_id: str
    user_id: str = "default_researcher"
    name: str
    description: str
    strategy_type: StrategyType = StrategyType.FIXED_STAKE
    platform_id: str = "1xbet"
    provider_id: str = "spribe"
    game_id: str = "aviator"
    room_id: str = "standard"
    target_multiplier: float = 2.0
    stake_sizing_method: StakeSizingMethod = StakeSizingMethod.FIXED_STAKE
    base_stake: float = 10.0
    stake_percentage: float = 2.0  # % of current bankroll
    max_stake_cap: float = 50.0
    model_id: Optional[str] = None
    min_model_confidence: float = 0.55
    risk_limits: RiskLimits = Field(default_factory=RiskLimits)
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimulatedTrade(BaseModel):
    trade_id: str
    simulation_id: str
    round_id: str
    round_index: int
    stake_amount: float
    target_cashout_multiplier: float
    actual_multiplier: float
    is_win: bool
    net_profit: float  # stake * (target - 1) if win else -stake
    bankroll_before: float
    bankroll_after: float
    drawdown_percent: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimulationPerformanceMetrics(BaseModel):
    total_rounds: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    starting_bankroll: float = 1000.0
    current_bankroll: float = 1000.0
    net_pnl: float = 0.0
    return_percentage: float = 0.0
    max_drawdown_percent: float = 0.0
    current_drawdown_percent: float = 0.0
    consecutive_wins_max: int = 0
    consecutive_losses_max: int = 0
    profit_factor: float = 0.0
    average_stake: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    risk_limit_breaches: List[str] = Field(default_factory=list)


class SimulationRecord(BaseModel):
    simulation_id: str
    user_id: str = "default_researcher"
    name: str
    mode: SimulationMode = SimulationMode.HISTORICAL_BACKTEST
    strategy: SimulationStrategy
    dataset_id: str = "ds-1xbet-aviator-standard"
    status: SimulationStatus = SimulationStatus.CREATED
    starting_virtual_bankroll: float = 1000.0
    current_virtual_bankroll: float = 1000.0
    metrics: SimulationPerformanceMetrics = Field(default_factory=SimulationPerformanceMetrics)
    trades: List[SimulatedTrade] = Field(default_factory=list)
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    stop_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateSimulationRequest(BaseModel):
    name: str
    mode: SimulationMode = SimulationMode.HISTORICAL_BACKTEST
    strategy_id: Optional[str] = None
    dataset_id: str = "ds-1xbet-aviator-standard"
    starting_virtual_bankroll: float = Field(1000.0, gt=0)
    strategy_config: Optional[Dict[str, Any]] = None


class MonteCarloRequest(BaseModel):
    job_name: str
    num_trials: int = Field(500, ge=10, le=5000)
    rounds_per_trial: int = Field(200, ge=20, le=2000)
    starting_bankroll: float = Field(1000.0, gt=0)
    stake_amount: float = Field(10.0, gt=0)
    target_multiplier: float = Field(2.0, ge=1.01)
    house_edge: float = Field(0.01, ge=0.0, le=0.10)
    max_drawdown_limit: float = Field(50.0, ge=5.0, le=100.0)
    random_seed: Optional[int] = 42


class MonteCarloResult(BaseModel):
    job_id: str
    job_name: str
    num_trials: int
    rounds_per_trial: int
    starting_bankroll: float
    median_final_bankroll: float
    mean_final_bankroll: float
    percentile_5th: float
    percentile_95th: float
    probability_of_ruin_percent: float
    probability_drawdown_breach_percent: float
    max_observed_drawdown: float
    sample_trajectories: List[List[float]] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scientific_disclaimer: str = (
        "HYPOTHETICAL MONTE CARLO SCENARIO ANALYSIS. "
        "Calculated assuming theoretical IID memoryless crash distribution. "
        "Does not constitute financial advice or predict future outcomes."
    )

