"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  Cpu,
  Download,
  Filter,
  AlertCircle,
  HelpCircle,
  RefreshCw,
  FileCheck,
  CheckCircle2,
  XCircle,
  Play,
  ShieldAlert,
} from "lucide-react";

export default function PredictionHistoryPage() {
  const [estimates, setEstimates] = useState<any[]>([]);
  const [scoredOutcomes, setScoredOutcomes] = useState<any[]>([]);
  const [evalSummary, setEvalSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [estData, outcomesData, summaryData] = await Promise.all([
        api.getResearchEstimates().catch(() => []),
        api.getScoredOutcomes(50).catch(() => []),
        api.getEvaluationsSummary().catch(() => null),
      ]);
      setEstimates(estData);
      setScoredOutcomes(outcomesData);
      setEvalSummary(summaryData);
    } catch (err) {
      console.error("Error loading prediction audit data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunEstimate = async () => {
    setEvaluating(true);
    setStatusMsg("Requesting research estimate from active model registry...");
    try {
      const payload = {
        platform_id: "1xbet",
        provider_id: "spribe",
        game_id: "aviator",
        room_id: "standard",
        target_threshold: 2.0,
        recent_multipliers: [1.15, 1.42, 2.15, 1.08, 1.95, 3.2, 1.25, 2.05, 1.18, 1.04, 4.1],
      };
      const res = await api.runResearchEstimate(payload);
      setStatusMsg(`Research estimate generated: P(>=2.0x) = ${(res.predicted_probability * 100).toFixed(1)}%`);
      await loadData();
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to generate research estimate.");
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Prediction Analysis & Calibration History"
          description="Audit log of generated mathematical research estimates and model forecasts compared strictly against observed historical ground truth."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Analytics", href: "/analytics" },
            { label: "Prediction History" },
          ]}
          action={
            <div className="flex items-center gap-3">
              <button
                onClick={handleRunEstimate}
                disabled={evaluating}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {evaluating ? "Evaluating..." : "Run Research Estimate"}
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
          <div className="p-3 rounded-lg bg-[#111827] border border-[#263247] text-xs text-purple-300">
            {statusMsg}
          </div>
        )}

        {/* SCIENTIFIC MANDATE BANNER */}
        <div className="p-4 rounded-xl border border-purple-500/30 bg-purple-950/20 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-purple-400 mt-0.5 shrink-0" />
          <div className="text-xs space-y-1 text-slate-300">
            <span className="font-semibold text-purple-300">Experimental ML Research — Not a Guaranteed Prediction:</span>
            <p className="text-slate-400">
              Estimates represent conditional statistical survival probabilities under tested parametric hypotheses. Crash sequences operate on cryptographic PRNG / Provably Fair hash chains. Estimates must never be used for automated betting.
            </p>
          </div>
        </div>

        {/* AGGREGATE EVALUATION CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Total Scored Estimates</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {evalSummary?.scored_estimates ?? 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Pending: {evalSummary?.pending_estimates ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Average Brier Score Error</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {evalSummary?.brier_score?.toFixed(4) ?? "0.2500"}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Null Baseline: {evalSummary?.baseline_brier_score?.toFixed(4) ?? "0.2500"}
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Classification Accuracy</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {evalSummary?.accuracy ? `${(evalSummary.accuracy * 100).toFixed(1)}%` : "0.0%"}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Target threshold: 2.00x</div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Edge Verification Status</span>
            <div className="text-sm font-bold text-rose-400 mt-3 flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> NO EDGE DETECTED
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Consistent with memoryless CSPRNG</div>
          </div>
        </div>

        {/* PREDICTION TRACKING TABLE */}
        <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-100 font-semibold text-sm">
              <Cpu className="w-4 h-4 text-purple-400" />
              <span>Research Estimate & Ground Truth Audit Trail</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">{estimates.length} Total</span>
          </div>

          {loading && estimates.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" /> Loading prediction logs...
            </div>
          ) : estimates.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No research estimates recorded yet. Click &quot;Run Research Estimate&quot; above to evaluate against the active model registry.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-[#0D1220] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#263247]">
                  <tr>
                    <th className="py-2.5 px-3">Estimate ID</th>
                    <th className="py-2.5 px-3">Model</th>
                    <th className="py-2.5 px-3">Target</th>
                    <th className="py-2.5 px-3">Predicted P</th>
                    <th className="py-2.5 px-3">Actual Result</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Brier Error</th>
                    <th className="py-2.5 px-3">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#263247]/60">
                  {estimates.map((e) => (
                    <tr key={e.estimate_id} className="hover:bg-[#0D1220]/50 transition">
                      <td className="py-2.5 px-3 font-mono text-purple-300 font-semibold">
                        {e.estimate_id}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">{e.model_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-200">{e.target_threshold}x</td>
                      <td className="py-2.5 px-3 font-bold text-slate-100">
                        {(e.predicted_probability * 100).toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 font-bold">
                        {e.actual_multiplier != null ? (
                          <span className={e.actual_multiplier >= e.target_threshold ? "text-emerald-400" : "text-slate-300"}>
                            {e.actual_multiplier.toFixed(2)}x
                          </span>
                        ) : (
                          <span className="text-slate-500 italic">Pending round...</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <StatusBadge
                          status={e.status === "SCORED" ? "VERIFIED" : e.status === "PENDING_OUTCOME" ? "STANDBY" : "REJECTED"}
                        />
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                        {e.brier_error != null ? e.brier_error.toFixed(4) : "—"}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                        {new Date(e.estimate_timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
