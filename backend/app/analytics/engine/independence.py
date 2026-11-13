"""Autocorrelation, Ljung-Box, and Statistical Independence Diagnostics."""
import math
from typing import List, Dict, Any
import numpy as np
from scipy import stats
from backend.app.analytics.schemas.analytics import (
    AutocorrelationResponse,
    AutocorrelationLag,
    IndependenceTestResult,
)


class IndependenceEngine:
    """Rigorous serial correlation and independence hypothesis tests."""

    @classmethod
    def compute(
        cls,
        dataset_id: str,
        multipliers: List[float],
        max_lags: int = 15
    ) -> AutocorrelationResponse:
        n = len(multipliers)
        if n < 10:
            return AutocorrelationResponse(
                dataset_id=dataset_id,
                sample_size=n,
                lags=[],
                ljung_box=None
            )

        arr = np.array(multipliers, dtype=np.float64)
        mean_val = np.mean(arr)
        centered = arr - mean_val
        c0 = np.dot(centered, centered) / n

        confidence_bound = round(1.95996 / math.sqrt(n), 4)
        lags_data: List[AutocorrelationLag] = []

        q_stat = 0.0
        # Compute ACF up to max_lags
        actual_lags = min(max_lags, n // 3)
        for k in range(1, actual_lags + 1):
            ck = np.dot(centered[:-k], centered[k:]) / n
            rk = ck / c0 if c0 > 0 else 0.0
            stat_sig = abs(rk) > confidence_bound
            lags_data.append(
                AutocorrelationLag(
                    lag=k,
                    autocorrelation=round(float(rk), 4),
                    confidence_bound=confidence_bound,
                    statistically_significant=stat_sig
                )
            )
            # Ljung-Box partial sum accumulation: Q = n*(n+2) * sum(r_k^2 / (n-k))
            q_stat += (rk ** 2) / (n - k)

        # Ljung-Box test statistic
        q_stat = q_stat * n * (n + 2)
        p_val = 1.0 - stats.chi2.cdf(q_stat, df=actual_lags) if actual_lags > 0 else 1.0

        reject = bool(p_val < 0.05)
        interp = (
            "Serial correlation detected across tested lags; rejection of independence."
            if reject
            else "Failure to reject null hypothesis; sequential round outcomes are consistent with independent random noise."
        )

        ljung_box_res = IndependenceTestResult(
            test_name="Ljung-Box Portmanteau Test for Serial Dependence",
            null_hypothesis="Rounds exhibit independent and identically distributed (IID) outcomes (Zero serial autocorrelation).",
            alternative_hypothesis="At least one lag exhibits non-zero autocorrelation.",
            test_statistic=round(float(q_stat), 4),
            p_value=round(float(p_val), 5),
            sample_size=n,
            significance_threshold=0.05,
            reject_null=reject,
            interpretation=interp,
            limitations=(
                "Failure to reject independence does not prove independence. "
                "CSPRNG commitments generate pseudorandom streams indistinguishable from theoretical IID random noise."
            )
        )

        return AutocorrelationResponse(
            dataset_id=dataset_id,
            sample_size=n,
            lags=lags_data,
            ljung_box=ljung_box_res
        )

    @classmethod
    def runs_test(cls, multipliers: List[float]) -> IndependenceTestResult:
        """Wald-Wolfowitz Runs Test for non-randomness."""
        n = len(multipliers)
        if n < 20:
            return IndependenceTestResult(
                test_name="Wald-Wolfowitz Runs Test",
                null_hypothesis="Sequence was produced by a random Bernoulli process.",
                alternative_hypothesis="Sequence exhibits non-random clustering or trend alternation.",
                test_statistic=0.0,
                p_value=1.0,
                sample_size=n,
                reject_null=False,
                interpretation="Sample size N < 20 is insufficient for Wald-Wolfowitz normal approximation.",
                limitations="Requires minimum 20 sequential round events."
            )

        med = np.median(multipliers)
        signs = [1 if x >= med else 0 for x in multipliers]
        n1 = sum(signs)
        n2 = n - n1

        # Count runs
        runs = 1
        for i in range(1, len(signs)):
            if signs[i] != signs[i - 1]:
                runs += 1

        # Expected runs and variance under null
        exp_runs = ((2 * n1 * n2) / n) + 1
        var_runs = ((2 * n1 * n2) * (2 * n1 * n2 - n)) / ((n ** 2) * (n - 1)) if n > 1 else 1.0
        z_stat = (runs - exp_runs) / math.sqrt(var_runs) if var_runs > 0 else 0.0
        p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        reject = bool(p_val < 0.05)
        return IndependenceTestResult(
            test_name="Wald-Wolfowitz Runs Test",
            null_hypothesis="Binary above/below median outcomes occur randomly.",
            alternative_hypothesis="Non-random clustering or alternating runs detected.",
            test_statistic=round(float(z_stat), 4),
            p_value=round(float(p_val), 5),
            sample_size=n,
            reject_null=reject,
            interpretation="Sequence is consistent with random process." if not reject else "Run count differs from random expectation.",
            limitations="Sensitive only to median partitioning; does not capture continuous multiplier tail behavior."
        )

