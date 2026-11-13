"""
Paper Trading Simulation Execution Engine & Manager.
Supports:
- Historical Backtesting on isolated datasets
- Replay Simulation at variable speeds
- Real-Time Live Paper Simulation linked to Phase 7 live feeds
Enforces zero lookahead bias and records immutable simulated positions.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from backend.app.simulation.schemas import (
    SimulationRecord,
    SimulationStrategy,
    SimulationStatus,
    SimulationMode,
    SimulatedTrade,
    SimulationPerformanceMetrics,
    CreateSimulationRequest,
    StrategyType,
)
from backend.app.simulation.bankroll_manager import BankrollManager
from backend.app.datasets.manager import dataset_manager
from backend.app.core.logging import logger


class SimulationManager:
    """Manages paper trading simulations, strategies, and execution lifecycles."""

    _instance: Optional["SimulationManager"] = None

    def __init__(self):
        self.simulations: Dict[str, SimulationRecord] = {}
        self.strategies: Dict[str, SimulationStrategy] = {}
        self._init_default_strategies()

    @classmethod
    def get_instance(cls) -> "SimulationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_default_strategies(self):
        """Seed standard research strategies."""
        s1 = SimulationStrategy(
            strategy_id="strat-fixed-2x",
            name="Conservative 2.00x Fixed Stake",
            description="Places a flat 10.0 virtual stake targeting 2.00x cashout.",
            strategy_type=StrategyType.FIXED_STAKE,
            target_multiplier=2.0,
            base_stake=10.0,
            platform_id="1xbet",
            provider_id="spribe"
        )
        s2 = SimulationStrategy(
            strategy_id="strat-dynamic-pct-1-5x",
            name="Dynamic 2% Bankroll @ 1.50x",
            description="Allocates 2% of current virtual bankroll targeting moderate 1.50x multiplier.",
            strategy_type=StrategyType.FIXED_PERCENTAGE,
            target_multiplier=1.5,
            stake_percentage=2.0,
            max_stake_cap=50.0,
            platform_id="1xbet",
            provider_id="spribe"
        )
        self.strategies[s1.strategy_id] = s1
        self.strategies[s2.strategy_id] = s2

    def create_strategy(self, strategy: SimulationStrategy) -> SimulationStrategy:
        self.strategies[strategy.strategy_id] = strategy
        return strategy

    def list_strategies(self) -> List[SimulationStrategy]:
        return list(self.strategies.values())

    def get_strategy(self, strategy_id: str) -> Optional[SimulationStrategy]:
        return self.strategies.get(strategy_id)

    def create_simulation(self, req: CreateSimulationRequest) -> SimulationRecord:
        sim_id = f"sim_{uuid.uuid4().hex[:10]}"

        # Resolve or create strategy
        strategy = None
        if req.strategy_id and req.strategy_id in self.strategies:
            strategy = self.strategies[req.strategy_id]
        elif req.strategy_config:
            strategy = SimulationStrategy(
                strategy_id=f"strat_{uuid.uuid4().hex[:8]}",
                name=req.strategy_config.get("name", "Custom Research Strategy"),
                description=req.strategy_config.get("description", "User-configured simulation strategy"),
                target_multiplier=float(req.strategy_config.get("target_multiplier", 2.0)),
                base_stake=float(req.strategy_config.get("base_stake", 10.0)),
                stake_percentage=float(req.strategy_config.get("stake_percentage", 2.0)),
            )
            self.strategies[strategy.strategy_id] = strategy
        else:
            strategy = list(self.strategies.values())[0]

        record = SimulationRecord(
            simulation_id=sim_id,
            name=req.name,
            mode=req.mode,
            strategy=strategy,
            dataset_id=req.dataset_id,
            status=SimulationStatus.CONFIGURED,
            starting_virtual_bankroll=req.starting_virtual_bankroll,
            current_virtual_bankroll=req.starting_virtual_bankroll,
            metrics=SimulationPerformanceMetrics(
                starting_bankroll=req.starting_virtual_bankroll,
                current_bankroll=req.starting_virtual_bankroll,
            )
        )
        self.simulations[sim_id] = record
        return record

    async def run_historical_backtest(self, simulation_id: str) -> SimulationRecord:
        """
        Executes chronological backtest on genuine historical dataset rounds.
        Enforces zero future leakage (target round result is evaluated strictly post-decision).
        """
        sim = self.simulations.get(simulation_id)
        if not sim:
            raise ValueError(f"Simulation '{simulation_id}' not found.")

        sim.status = SimulationStatus.RUNNING
        sim.start_timestamp = datetime.now(timezone.utc)

        # 1. Fetch rounds strictly chronologically
        rounds = await dataset_manager.get_dataset_rounds(sim.dataset_id)
        if len(rounds) == 0:
            sim.status = SimulationStatus.FAILED
            sim.stop_reason = "Dataset contains 0 records."
            return sim

        # Sort chronological (oldest to newest)
        sorted_rounds = sorted(rounds, key=lambda x: x.round_timestamp)

        bankroll_mgr = BankrollManager(
            starting_bankroll=sim.starting_virtual_bankroll,
            strategy=sim.strategy
        )

        trades: List[SimulatedTrade] = []
        consec_losses_max = 0
        consec_wins_max = 0
        largest_win = 0.0
        largest_loss = 0.0

        for idx, r in enumerate(sorted_rounds):
            # Check risk limits prior to position
            ok_limits, breach_reason = bankroll_mgr.check_risk_limits()
            if not ok_limits:
                sim.stop_reason = breach_reason
                sim.metrics.risk_limit_breaches.append(breach_reason)
                break

            # Calculate stake
            ok_stake, stake_err, stake_amount = bankroll_mgr.calculate_stake()
            if not ok_stake:
                sim.stop_reason = stake_err
                break

            bankroll_before = bankroll_mgr.current_bankroll

            # Evaluate outcome strictly against target cashout multiplier
            is_win, pnl = bankroll_mgr.record_outcome(
                stake=stake_amount,
                actual_multiplier=r.multiplier,
                target_multiplier=sim.strategy.target_multiplier
            )

            if pnl > largest_win:
                largest_win = pnl
            if pnl < largest_loss:
                largest_loss = pnl

            if bankroll_mgr.consecutive_losses > consec_losses_max:
                consec_losses_max = bankroll_mgr.consecutive_losses
            if bankroll_mgr.consecutive_wins > consec_wins_max:
                consec_wins_max = bankroll_mgr.consecutive_wins

            trade = SimulatedTrade(
                trade_id=f"trd_{sim.simulation_id}_{idx:04d}",
                simulation_id=sim.simulation_id,
                round_id=r.round_id,
                round_index=idx + 1,
                stake_amount=stake_amount,
                target_cashout_multiplier=sim.strategy.target_multiplier,
                actual_multiplier=r.multiplier,
                is_win=is_win,
                net_profit=pnl,
                bankroll_before=bankroll_before,
                bankroll_after=bankroll_mgr.current_bankroll,
                drawdown_percent=bankroll_mgr.get_current_drawdown_percent(),
                timestamp=r.round_timestamp
            )
            trades.append(trade)

        # Update metrics
        total = len(trades)
        wins = sum(1 for t in trades if t.is_win)
        losses = total - wins
        win_rate = (wins / total) if total > 0 else 0.0
        net_pnl = round(bankroll_mgr.current_bankroll - sim.starting_virtual_bankroll, 2)
        ret_pct = round((net_pnl / sim.starting_virtual_bankroll) * 100.0, 2)

        gross_wins = sum(t.net_profit for t in trades if t.is_win)
        gross_losses = abs(sum(t.net_profit for t in trades if not t.is_win))
        profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else 0.0

        max_dd = max([t.drawdown_percent for t in trades], default=0.0)
        avg_stake = round(sum(t.stake_amount for t in trades) / total, 2) if total > 0 else 0.0

        sim.trades = trades
        sim.current_virtual_bankroll = bankroll_mgr.current_bankroll
        sim.metrics = SimulationPerformanceMetrics(
            total_rounds=total,
            wins=wins,
            losses=losses,
            win_rate=round(win_rate, 4),
            starting_bankroll=sim.starting_virtual_bankroll,
            current_bankroll=bankroll_mgr.current_bankroll,
            net_pnl=net_pnl,
            return_percentage=ret_pct,
            max_drawdown_percent=round(max_dd, 2),
            current_drawdown_percent=bankroll_mgr.get_current_drawdown_percent(),
            consecutive_wins_max=consec_wins_max,
            consecutive_losses_max=consec_losses_max,
            profit_factor=profit_factor,
            average_stake=avg_stake,
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            risk_limit_breaches=sim.metrics.risk_limit_breaches,
        )

        sim.status = SimulationStatus.COMPLETED
        sim.end_timestamp = datetime.now(timezone.utc)
        return sim

    def pause_simulation(self, simulation_id: str) -> Optional[SimulationRecord]:
        sim = self.simulations.get(simulation_id)
        if sim and sim.status == SimulationStatus.RUNNING:
            sim.status = SimulationStatus.PAUSED
            return sim
        return None

    def resume_simulation(self, simulation_id: str) -> Optional[SimulationRecord]:
        sim = self.simulations.get(simulation_id)
        if sim and sim.status == SimulationStatus.PAUSED:
            sim.status = SimulationStatus.RUNNING
            return sim
        return None

    def stop_simulation(self, simulation_id: str) -> Optional[SimulationRecord]:
        sim = self.simulations.get(simulation_id)
        if sim:
            sim.status = SimulationStatus.CANCELLED
            sim.end_timestamp = datetime.now(timezone.utc)
            return sim
        return None

    def get_simulation(self, simulation_id: str) -> Optional[SimulationRecord]:
        return self.simulations.get(simulation_id)

    def list_simulations(self) -> List[SimulationRecord]:
        return sorted(list(self.simulations.values()), key=lambda x: x.created_at, reverse=True)

