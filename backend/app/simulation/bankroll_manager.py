"""
Virtual Bankroll Management & Risk Limit Enforcement.
Calculates dynamic stake sizing (Fixed, Percentage, Capped Percentage),
enforces stop-loss and maximum drawdown constraints, and prevents negative virtual balances.
"""

from typing import Tuple, Optional
from backend.app.simulation.schemas import (
    RiskLimits,
    StakeSizingMethod,
    SimulationStrategy,
)


class BankrollManager:
    """Manages virtual bankroll state, stake computation, and strict risk guardrails."""

    def __init__(self, starting_bankroll: float, strategy: SimulationStrategy):
        if starting_bankroll <= 0:
            raise ValueError(f"Starting bankroll must be positive: {starting_bankroll}")

        self.starting_bankroll = float(starting_bankroll)
        self.current_bankroll = float(starting_bankroll)
        self.peak_bankroll = float(starting_bankroll)
        self.strategy = strategy
        self.limits: RiskLimits = strategy.risk_limits
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.total_rounds = 0

    def calculate_stake(self) -> Tuple[bool, Optional[str], float]:
        """
        Calculates stake amount based on strategy sizing rule.
        Returns (is_valid, rejection_reason, stake_amount).
        """
        if self.current_bankroll <= 0:
            return False, "Virtual bankroll depleted (0.00).", 0.0

        method = self.strategy.stake_sizing_method
        base = self.strategy.base_stake
        pct = self.strategy.stake_percentage / 100.0

        if method == StakeSizingMethod.FIXED_STAKE:
            proposed = base
        elif method == StakeSizingMethod.PERCENTAGE_OF_BANKROLL:
            proposed = self.current_bankroll * pct
        elif method == StakeSizingMethod.CAPPED_PERCENTAGE:
            proposed = min(self.current_bankroll * pct, self.strategy.max_stake_cap)
        else:
            proposed = base

        # Enforce minimum & maximum stake bounds
        proposed = max(self.limits.min_stake, min(proposed, self.limits.max_stake))

        # Check if bankroll can cover stake
        if proposed > self.current_bankroll:
            proposed = self.current_bankroll

        if proposed <= 0:
            return False, "Calculated stake is non-positive or exceeds available balance.", 0.0

        return True, None, round(proposed, 2)

    def check_risk_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether current state breaches configured risk limits.
        Returns (is_ok, breach_reason).
        """
        # 1. Total depletion
        if self.current_bankroll <= 0:
            return False, "RISK LIMIT BREACH: Virtual bankroll completely depleted."

        # 2. Maximum Drawdown Check
        drawdown_pct = 0.0
        if self.peak_bankroll > 0:
            drawdown_pct = ((self.peak_bankroll - self.current_bankroll) / self.peak_bankroll) * 100.0

        if drawdown_pct >= self.limits.max_drawdown_percent:
            return False, f"RISK LIMIT BREACH: Drawdown reached {drawdown_pct:.1f}% (Limit: {self.limits.max_drawdown_percent}%)."

        # 3. Maximum consecutive losses
        if self.consecutive_losses >= self.limits.max_consecutive_losses:
            return False, f"RISK LIMIT BREACH: Reached {self.consecutive_losses} consecutive simulated losses."

        # 4. Maximum simulated rounds
        if self.total_rounds >= self.limits.max_simulated_rounds:
            return False, f"LIMIT REACHED: Completed maximum configured simulated rounds ({self.limits.max_simulated_rounds})."

        return True, None

    def record_outcome(self, stake: float, actual_multiplier: float, target_multiplier: float) -> Tuple[bool, float]:
        """
        Updates bankroll after round outcome.
        Returns (is_win, net_profit).
        """
        self.total_rounds += 1
        is_win = (actual_multiplier >= target_multiplier)

        if is_win:
            net_profit = stake * (target_multiplier - 1.0)
            self.current_bankroll += net_profit
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            if self.current_bankroll > self.peak_bankroll:
                self.peak_bankroll = self.current_bankroll
        else:
            net_profit = -stake
            self.current_bankroll = max(0.0, self.current_bankroll - stake)
            self.consecutive_losses += 1
            self.consecutive_wins = 0

        self.current_bankroll = round(self.current_bankroll, 2)
        return is_win, round(net_profit, 2)

    def get_current_drawdown_percent(self) -> float:
        if self.peak_bankroll <= 0:
            return 0.0
        return round(((self.peak_bankroll - self.current_bankroll) / self.peak_bankroll) * 100.0, 2)

