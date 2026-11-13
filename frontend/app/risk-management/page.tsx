"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/services/apiClient";
import {
  ShieldAlert,
  Sliders,
  AlertTriangle,
  StopCircle,
  TrendingDown,
  RefreshCw,
  Coins,
  Dna,
  Play,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export default function RiskManagementPage() {
  const [riskOverview, setRiskOverview] = useState<any | null>(null);
  const [mcResult, setMcResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningMc, setRunningMc] = useState<boolean>(false);
  const [mcMsg, setMcMsg] = useState<string>("");

  // Monte Carlo parameters
  const [trials, setTrials] = useState<number>(300);
  const [roundsPerTrial, setRoundsPerTrial] = useState<number>(100);
  const [startBankroll, setStartBankroll] = useState<number>(1000.0);
  const [stake, setStake] = useState<number>(10.0);
  const [targetMultiplier, setTargetMultiplier] = useState<number>(2.0);

  const fetchRisk = async () => {
    try {
      setLoading(true);
      const data = await api.getRiskOverview().catch(() => null);
      setRiskOverview(data);
    } catch (err) {
      console.error("Error loading risk overview:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRisk();
  }, []);

  const handleRunMonteCarlo = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunningMc(true);
    setMcMsg("Vectorizing hypothetical Monte Carlo crash sequences...");
    try {
      const payload = {
        job_name: `MC Analysis @ ${targetMultiplier}x`,
        num_trials: Number(trials),
        rounds_per_trial: Number(roundsPerTrial),
        starting_bankroll: Number(startBankroll),
        stake_amount: Number(stake),
        target_multiplier: Number(targetMultiplier),
        house_edge: 0.01,
        max_drawdown_limit: 40.0,
        random_seed: 42,
      };
      const res = await api.runMonteCarlo(payload);
      setMcResult(res);
      setMcMsg(`Monte Carlo completed: Ruin probability = ${res.probability_of_ruin_percent}%`);
    } catch (err: any) {
      setMcMsg(err.message || "Failed to execute Monte Carlo simulation.");
    } finally {
      setRunningMc(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Institutional Risk Guardrails & Safety Policy"
          description="Establish mandatory loss limits, drawdown circuit-breakers, and session exposure caps to eliminate gambler's ruin and loss-chasing patterns."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Simulation", href: "/paper-trading" },
            { label: "Risk Management" },
          ]}
          action={
            <button
              onClick={fetchRisk}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#263247] bg-[#111827] text-xs font-semibold text-slate-300 hover:bg-[#0D1220] transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Risk Telemetry
            </button>
          }
        />

        {/* SCIENTIFIC MANDATE BANNER */}
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
          <div className="text-xs space-y-1 text-slate-300">
            <span className="font-semibold text-rose-300">Gambler&apos;s Fallacy & Loss Chasing Prohibitions:</span>
            <p className="text-slate-400">
              The engine strictly prohibits progressive loss-chasing (Martingale). Past losses do not create an edge on future rounds. Configured risk stops enforce immediate execution halts upon hitting maximum drawdown limits.
            </p>
          </div>
        </div>

        {/* RISK TELEMETRY OVERVIEW CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Total Paper Simulations</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {riskOverview?.total_simulations ?? 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Active Positions: {riskOverview?.total_simulated_positions ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Max Observed Drawdown</span>
            <div className="text-2xl font-bold text-amber-400 mt-2">
              {riskOverview?.max_observed_drawdown_percent?.toFixed(1) ?? "0.0"}%
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Across all paper runs</div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Risk Circuit Breaches</span>
            <div className="text-2xl font-bold text-rose-400 mt-2">
              {riskOverview?.total_risk_limit_breaches ?? 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Enforced safety stops</div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Circuit Breaker Status</span>
            <div className="text-sm font-bold text-emerald-400 mt-3 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> ARMED & ACTIVE
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Automated execution halt</div>
          </div>
        </div>

        {/* MONTE CARLO RISK SIMULATION LAB */}
        <div className="rounded-xl border border-[#263247] bg-[#111827] p-6 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#263247] pb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Dna className="w-4 h-4 text-purple-400" />
                <span>Monte Carlo Risk & Ruin Analysis Lab</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Simulate hundreds of parallel hypothetical trajectories under a theoretical memoryless crash distribution to evaluate long-term bankroll survival.
              </p>
            </div>
          </div>

          <form onSubmit={handleRunMonteCarlo} className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Simulated Trials</label>
              <input
                type="number"
                min={20}
                max={2000}
                value={trials}
                onChange={(e) => setTrials(Number(e.target.value))}
                className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Rounds per Trial</label>
              <input
                type="number"
                min={20}
                max={500}
                value={roundsPerTrial}
                onChange={(e) => setRoundsPerTrial(Number(e.target.value))}
                className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Start Bankroll ($)</label>
              <input
                type="number"
                min={100}
                value={startBankroll}
                onChange={(e) => setStartBankroll(Number(e.target.value))}
                className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Fixed Stake ($)</label>
              <input
                type="number"
                min={1}
                value={stake}
                onChange={(e) => setStake(Number(e.target.value))}
                className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={runningMc}
                className="w-full py-2 px-4 rounded-lg bg-purple-600 hover:bg-purple-500 font-semibold text-white transition disabled:opacity-50 flex items-center justify-center gap-1.5"
              >
                {runningMc ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                Run Monte Carlo
              </button>
            </div>
          </form>

          {mcMsg && (
            <div className="p-3 rounded-lg bg-[#0D1220] border border-[#263247] text-xs text-purple-300 font-mono">
              {mcMsg}
            </div>
          )}

          {mcResult && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                  <span className="text-[11px] text-slate-400">Risk of Ruin (0.00 Balance)</span>
                  <div className="text-xl font-bold text-rose-400 mt-1">
                    {mcResult.probability_of_ruin_percent}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Under stated stake rule</div>
                </div>

                <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                  <span className="text-[11px] text-slate-400">Drawdown Breach Risk (40%)</span>
                  <div className="text-xl font-bold text-amber-400 mt-1">
                    {mcResult.probability_drawdown_breach_percent}%
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Threshold violation probability</div>
                </div>

                <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                  <span className="text-[11px] text-slate-400">Median Final Bankroll</span>
                  <div className="text-xl font-bold text-slate-100 mt-1">
                    ${mcResult.median_final_bankroll.toFixed(2)}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Mean: ${mcResult.mean_final_bankroll.toFixed(2)}</div>
                </div>

                <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                  <span className="text-[11px] text-slate-400">5th – 95th Percentile Spread</span>
                  <div className="text-base font-bold text-slate-200 mt-1">
                    ${mcResult.percentile_5th.toFixed(0)} – ${mcResult.percentile_95th.toFixed(0)}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Outcome distribution band</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
