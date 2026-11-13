"use client";

import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { ChartCard } from "@/components/ui/ChartCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { SlidersHorizontal, ShieldCheck, Check, AlertCircle } from "lucide-react";

export default function StrategiesPage() {
  return (
    <AppShell>
      <PageHeader
        title="Simulation Strategy Laboratory"
        description="Compare disciplined mathematical exit strategies: Fixed Multiplier, Dynamic Fractional Kelly, and Volatility Targeting. Loss-chasing algorithms are permanently prohibited."
        breadcrumbs={[
          { label: "Simulation" },
          { label: "Paper Trading", href: "/paper-trading" },
          { label: "Strategy Laboratory" },
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-5 rounded-xl border border-border">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-foreground">Fixed Exit Multiplier</h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active
            </span>
          </div>
          <p className="text-xs text-muted mb-4">
            Static exit trigger at fixed threshold (e.g. 1.50x or 2.00x) with invariant sizing.
          </p>
          <div className="text-[11px] text-muted space-y-1">
            <div className="flex justify-between">
              <span>Risk Profile:</span>
              <span className="text-foreground font-semibold">Low</span>
            </div>
            <div className="flex justify-between">
              <span>Mathematical Expectation:</span>
              <span className="text-foreground font-mono">1 - HouseEdge</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-border">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-foreground">Fractional Kelly Criterion</h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Research
            </span>
          </div>
          <p className="text-xs text-muted mb-4">
            Scales stake size proportionally to estimated edge. Zero stake allocated if no edge detected.
          </p>
          <div className="text-[11px] text-muted space-y-1">
            <div className="flex justify-between">
              <span>Risk Profile:</span>
              <span className="text-foreground font-semibold">Moderate</span>
            </div>
            <div className="flex justify-between">
              <span>Stake Constraint:</span>
              <span className="text-foreground font-mono">Max 1.0%</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-danger/30 bg-danger/5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-foreground">Martingale / Doubling</h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-danger/20 text-danger border border-danger/40">
              Prohibited
            </span>
          </div>
          <p className="text-xs text-muted mb-4">
            Doubling stakes after losses guarantees catastrophic tail risk and account drawdown.
          </p>
          <div className="p-2 rounded bg-surface-muted/60 text-[11px] text-danger font-semibold">
            System Guardrail: Algorithm is disabled by application risk policy.
          </div>
        </div>
      </div>

      <ChartCard
        title="Simulated Strategy Comparison"
        subtitle="Historical backtest comparison of allowed rules"
      >
        <EmptyState
          title="Backtest Pipeline Standby"
          description="Select verified historical datasets from the Historical Rounds explorer to execute comparative strategy backtests."
          icon="database"
        />
      </ChartCard>
    </AppShell>
  );
}

