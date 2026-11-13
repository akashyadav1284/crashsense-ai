"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  Coins,
  Play,
  Pause,
  RotateCcw,
  ShieldAlert,
  Wallet,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Plus,
  Sliders,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";

export default function PaperTradingPage() {
  const [simulations, setSimulations] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [selectedSim, setSelectedSim] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>("");

  // Create Modal / Form State
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [simName, setSimName] = useState<string>("Aviator Backtest Alpha");
  const [mode, setMode] = useState<string>("HISTORICAL_BACKTEST");
  const [startBankroll, setStartBankroll] = useState<number>(1000.0);
  const [targetCashout, setTargetCashout] = useState<number>(2.0);
  const [baseStake, setBaseStake] = useState<number>(10.0);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sims, strats] = await Promise.all([
        api.getSimulations().catch(() => []),
        api.getStrategies().catch(() => []),
      ]);
      setSimulations(sims);
      setStrategies(strats);
      if (sims.length > 0 && !selectedSim) {
        setSelectedSim(sims[0]);
      }
    } catch (err) {
      console.error("Failed to load paper trading simulations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: simName,
        mode,
        dataset_id: "ds-1xbet-aviator-standard",
        starting_virtual_bankroll: Number(startBankroll),
        strategy_config: {
          name: `${simName} Strategy`,
          description: `Custom ${mode} rule with ${targetCashout}x cashout`,
          target_multiplier: Number(targetCashout),
          base_stake: Number(baseStake),
        },
      };
      const created = await api.createSimulation(payload);
      setIsCreating(false);
      await loadData();
      setSelectedSim(created);
      setStatusMsg(`Simulation "${created.name}" configured.`);
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to create simulation.");
    }
  };

  const handleStartBacktest = async () => {
    if (!selectedSim) return;
    setRunning(true);
    setStatusMsg(`Executing historical backtest on dataset "${selectedSim.dataset_id}"...`);
    try {
      const updated = await api.startSimulation(selectedSim.simulation_id);
      setSelectedSim(updated);
      await loadData();
      setStatusMsg(
        `Simulation completed! Processed ${updated.metrics.total_rounds} rounds. Virtual P/L: $${updated.metrics.net_pnl.toFixed(2)}`
      );
    } catch (err: any) {
      setStatusMsg(err.message || "Backtest execution failed.");
    } finally {
      setRunning(false);
    }
  };

  const handleStopSimulation = async () => {
    if (!selectedSim) return;
    try {
      const stopped = await api.stopSimulation(selectedSim.simulation_id);
      setSelectedSim(stopped);
      await loadData();
      setStatusMsg("Simulation terminated.");
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to stop simulation.");
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Paper Trading & Execution Simulation"
          description="Dry-run trading sandbox strictly utilizing virtual balances to stress-test mathematical cashout rules without real-money execution."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Simulation", href: "/paper-trading" },
            { label: "Paper Trading" },
          ]}
          action={
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsCreating(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition"
              >
                <Plus className="w-3.5 h-3.5" /> New Simulation
              </button>
              <button
                onClick={loadData}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#263247] bg-[#111827] text-xs font-semibold text-slate-300 hover:bg-[#0D1220] transition"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>
          }
        />

        {statusMsg && (
          <div className="p-3 rounded-lg bg-[#111827] border border-[#263247] text-xs text-purple-300 font-mono">
            {statusMsg}
          </div>
        )}

        {/* SIMULATION MANDATE BANNER */}
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs space-y-1 text-slate-300">
            <span className="font-semibold text-amber-300">Strict Simulation & Research Sandbox:</span>
            <p className="text-slate-400">
              All balances, stakes, and profits displayed here are entirely <strong>VIRTUAL</strong>. Real-money betting, automated wagering, and interaction with betting operator accounts are strictly prohibited.
            </p>
          </div>
        </div>

        {/* CREATE MODAL */}
        {isCreating && (
          <div className="p-5 rounded-xl border border-purple-500/40 bg-[#111827] space-y-4">
            <div className="flex items-center justify-between border-b border-[#263247] pb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                <span>Configure Paper Trading Simulation</span>
              </h3>
              <button
                onClick={() => setIsCreating(false)}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                ✕ Cancel
              </button>
            </div>

            <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Simulation Name</label>
                <input
                  type="text"
                  value={simName}
                  onChange={(e) => setSimName(e.target.value)}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Simulation Mode</label>
                <select
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
                >
                  <option value="HISTORICAL_BACKTEST">Historical Backtest</option>
                  <option value="REPLAY_SIMULATION">Historical Replay (Variable Speed)</option>
                  <option value="LIVE_PAPER">Authorized Live Paper Simulation</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Starting Virtual Bankroll ($)</label>
                <input
                  type="number"
                  min={10}
                  step={10}
                  value={startBankroll}
                  onChange={(e) => setStartBankroll(Number(e.target.value))}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Target Cashout Multiplier</label>
                <input
                  type="number"
                  min={1.05}
                  step={0.05}
                  value={targetCashout}
                  onChange={(e) => setTargetCashout(Number(e.target.value))}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Virtual Base Stake ($)</label>
                <input
                  type="number"
                  min={1}
                  step={1}
                  value={baseStake}
                  onChange={(e) => setBaseStake(Number(e.target.value))}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none"
                  required
                />
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full py-2 px-4 rounded-lg bg-purple-600 hover:bg-purple-500 font-semibold text-white transition"
                >
                  Save & Initialize
                </button>
              </div>
            </form>
          </div>
        )}

        {/* SIMULATION WORKSPACE GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* SIMULATION LIST */}
          <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Coins className="w-4 h-4 text-purple-400" />
                <span>Simulations</span>
              </span>
              <span className="text-xs text-slate-400 font-mono">{simulations.length} Total</span>
            </div>

            {loading && simulations.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">Loading simulations...</div>
            ) : simulations.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No active simulations. Click &quot;New Simulation&quot; to configure one.
              </div>
            ) : (
              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {simulations.map((s) => {
                  const isSelected = selectedSim?.simulation_id === s.simulation_id;
                  return (
                    <div
                      key={s.simulation_id}
                      onClick={() => setSelectedSim(s)}
                      className={`p-3 rounded-lg border transition cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "border-purple-500 bg-purple-950/20"
                          : "border-[#263247] bg-[#0D1220] hover:border-slate-600"
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="font-semibold text-xs text-slate-200">{s.name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          Bankroll: ${s.current_virtual_bankroll?.toFixed(2)} | P/L: $
                          {s.metrics?.net_pnl?.toFixed(2) ?? "0.00"}
                        </div>
                      </div>
                      <StatusBadge
                        status={s.status === "COMPLETED" ? "VERIFIED" : s.status === "RUNNING" ? "ACTIVE" : "STANDBY"}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ACTIVE SIMULATION DETAIL & METRICS */}
          <div className="lg:col-span-2 space-y-6">
            {selectedSim ? (
              <div className="rounded-xl border border-[#263247] bg-[#111827] p-6 space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#263247] pb-4">
                  <div>
                    <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                      <span>{selectedSim.name}</span>
                      <span className="text-xs font-mono text-purple-400">({selectedSim.simulation_id})</span>
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Mode: <span className="text-slate-300 font-mono">{selectedSim.mode}</span> | Strategy:{" "}
                      <span className="text-slate-300">{selectedSim.strategy?.name}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleStartBacktest}
                      disabled={running}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition disabled:opacity-50"
                    >
                      <Play className="w-3.5 h-3.5" />
                      {running ? "Running..." : "Run Backtest"}
                    </button>
                    <button
                      onClick={handleStopSimulation}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-500/40 bg-rose-950/30 hover:bg-rose-900/40 text-xs font-semibold text-rose-300 transition"
                    >
                      <RotateCcw className="w-3.5 h-3.5" /> Terminate
                    </button>
                  </div>
                </div>

                {/* METRICS CARDS */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                    <span className="text-[11px] text-slate-400">Virtual Bankroll</span>
                    <div className="text-xl font-bold text-slate-100 mt-1">
                      ${selectedSim.current_virtual_bankroll?.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      Start: ${selectedSim.starting_virtual_bankroll?.toFixed(2)}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                    <span className="text-[11px] text-slate-400">Net Virtual P/L</span>
                    <div
                      className={`text-xl font-bold mt-1 ${
                        (selectedSim.metrics?.net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      ${selectedSim.metrics?.net_pnl?.toFixed(2) ?? "0.00"}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      Return: {selectedSim.metrics?.return_percentage?.toFixed(1) ?? "0.0"}%
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                    <span className="text-[11px] text-slate-400">Win Rate</span>
                    <div className="text-xl font-bold text-slate-100 mt-1">
                      {selectedSim.metrics?.win_rate ? `${(selectedSim.metrics.win_rate * 100).toFixed(1)}%` : "0.0%"}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {selectedSim.metrics?.wins ?? 0}W / {selectedSim.metrics?.losses ?? 0}L
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                    <span className="text-[11px] text-slate-400">Max Drawdown</span>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {selectedSim.metrics?.max_drawdown_percent?.toFixed(1) ?? "0.0"}%
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      Peak: ${selectedSim.starting_virtual_bankroll?.toFixed(2)}
                    </div>
                  </div>
                </div>

                {/* RECENT TRADES AUDIT TABLE */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                    <span>Simulated Positions Audit ({selectedSim.trades?.length ?? 0} Rounds Executed)</span>
                    {selectedSim.stop_reason && (
                      <span className="text-rose-400 font-mono text-[11px]">{selectedSim.stop_reason}</span>
                    )}
                  </div>

                  {(!selectedSim.trades || selectedSim.trades.length === 0) ? (
                    <div className="py-8 text-center text-slate-500 text-xs bg-[#0D1220] rounded-lg border border-[#263247]">
                      No rounds processed yet. Click &quot;Run Backtest&quot; above to simulate chronological execution.
                    </div>
                  ) : (
                    <div className="overflow-x-auto max-h-[260px] overflow-y-auto">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-[#0D1220] text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-[#263247]">
                          <tr>
                            <th className="py-2 px-3">Round ID</th>
                            <th className="py-2 px-3">Stake</th>
                            <th className="py-2 px-3">Target</th>
                            <th className="py-2 px-3">Actual Multiplier</th>
                            <th className="py-2 px-3">Virtual P/L</th>
                            <th className="py-2 px-3">Ending Bankroll</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#263247]/50">
                          {selectedSim.trades.slice(-50).reverse().map((t: any) => (
                            <tr key={t.trade_id} className="hover:bg-[#0D1220]/40">
                              <td className="py-2 px-3 font-mono text-purple-300">{t.round_id}</td>
                              <td className="py-2 px-3 font-semibold text-slate-200">${t.stake_amount.toFixed(2)}</td>
                              <td className="py-2 px-3 text-slate-300">{t.target_cashout_multiplier}x</td>
                              <td className="py-2 px-3 font-bold text-slate-100">{t.actual_multiplier.toFixed(2)}x</td>
                              <td className={`py-2 px-3 font-bold ${t.is_win ? "text-emerald-400" : "text-rose-400"}`}>
                                {t.is_win ? `+$${t.net_profit.toFixed(2)}` : `-$${Math.abs(t.net_profit).toFixed(2)}`}
                              </td>
                              <td className="py-2 px-3 font-mono text-slate-300">${t.bankroll_after.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-16 text-center text-slate-500 text-xs border border-[#263247] rounded-xl bg-[#111827]">
                Select a simulation from the list on the left to view metrics and execution logs.
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
