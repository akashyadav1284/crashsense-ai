"""
Monte Carlo Simulation Engine for Research and Risk Analysis.
Simulates hypothetical bankroll trajectories under IID crash game distributions,
calculating probability of ruin, drawdown distributions, and risk limit breaches.
"""

import uuid
import numpy as np
from datetime import datetime, timezone
from typing import List
from backend.app.simulation.schemas import (
    MonteCarloRequest,
    MonteCarloResult,
)


class MonteCarloEngine:
    """Executes vectorized hypothetical Monte Carlo risk simulations."""

    @staticmethod
    def run_simulation(req: MonteCarloRequest) -> MonteCarloResult:
        job_id = f"mc_{uuid.uuid4().hex[:10]}"

        if req.random_seed is not None:
            np.random.seed(req.random_seed)

        # Theoretical crash distribution: P(M >= m) = (1 - h) / m
        p_win = max(0.001, min(0.999, (1.0 - req.house_edge) / req.target_multiplier))

        num_trials = req.num_trials
        rounds = req.rounds_per_trial
        stake = req.stake_amount
        target = req.target_multiplier
        start_bankroll = req.starting_bankroll
        max_dd_limit = req.max_drawdown_limit

        final_bankrolls: List[float] = []
        ruin_count = 0
        dd_breach_count = 0
        max_dds: List[float] = []
        sample_trajectories: List[List[float]] = []

        # Vectorized generation across trials
        # Bernoulli trial outcomes: 1 if win, 0 if loss
        random_wins = (np.random.uniform(0, 1, size=(num_trials, rounds)) < p_win).astype(int)

        # Profit multiplier per round
        win_profit = stake * (target - 1.0)
        loss_profit = -stake
        round_pnl = np.where(random_wins == 1, win_profit, loss_profit)

        # Compute trajectories
        for i in range(num_trials):
            balance = start_bankroll
            peak = start_bankroll
            max_dd = 0.0
            is_ruined = False
            is_dd_breached = False
            trajectory = [round(balance, 2)]

            for r in range(rounds):
                pnl = round_pnl[i, r]
                balance += pnl
                if balance <= 0:
                    balance = 0.0
                    is_ruined = True

                if balance > peak:
                    peak = balance

                dd = ((peak - balance) / peak) * 100.0 if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

                if dd >= max_dd_limit:
                    is_dd_breached = True

                if i < 8:  # store first 8 sample trajectories for charts
                    trajectory.append(round(balance, 2))

                if is_ruined:
                    # Pad remainder with 0.0
                    if i < 8:
                        trajectory.extend([0.0] * (rounds - r - 1))
                    break

            final_bankrolls.append(balance)
            max_dds.append(max_dd)
            if is_ruined:
                ruin_count += 1
            if is_dd_breached:
                dd_breach_count += 1
            if i < 8:
                sample_trajectories.append(trajectory)

        final_arr = np.array(final_bankrolls)
        median_val = float(np.median(final_arr))
        mean_val = float(np.mean(final_arr))
        p5 = float(np.percentile(final_arr, 5))
        p95 = float(np.percentile(final_arr, 95))
        p_ruin = (ruin_count / num_trials) * 100.0
        p_dd_breach = (dd_breach_count / num_trials) * 100.0
        max_observed_dd = float(np.max(max_dds))

        return MonteCarloResult(
            job_id=job_id,
            job_name=req.job_name,
            num_trials=num_trials,
            rounds_per_trial=rounds,
            starting_bankroll=start_bankroll,
            median_final_bankroll=round(median_val, 2),
            mean_final_bankroll=round(mean_val, 2),
            percentile_5th=round(p5, 2),
            percentile_95th=round(p95, 2),
            probability_of_ruin_percent=round(p_ruin, 2),
            probability_drawdown_breach_percent=round(p_dd_breach, 2),
            max_observed_drawdown=round(max_observed_dd, 2),
            sample_trajectories=sample_trajectories,
            executed_at=datetime.now(timezone.utc)
        )

