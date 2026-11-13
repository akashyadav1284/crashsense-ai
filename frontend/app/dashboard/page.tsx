"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { ChartCard } from "@/components/ui/ChartCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { api } from "@/services/apiClient";
import { HealthState } from "@/types";
import {
  Layers,
  Network,
  Database,
  History,
  CheckCircle2,
  Wallet,
  RefreshCw,
  Sliders,
  AlertTriangle,
} from "lucide-react";

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("24h");

  const loadData = () => {
    setLoading(true);
    api
      .getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Predictive Telemetry Overview"
        description="Multi-platform real-time multiplier intelligence, stream health, and quantitative risk guardrails."
        breadcrumbs={[{ label: "Overview" }, { label: "Dashboard" }]}
        action={
          <div className="flex items-center gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="1h">Last 1 Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
            <button
              onClick={loadData}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        }
      />

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Historical Rounds"
          value="Awaiting Data"
          subValue="Zero synthetic records"
          icon={Layers}
          badge="Empty"
          badgeType="neutral"
        />
        <StatCard
          title="Connected Platforms"
          value={health?.services.mongodb.status === "connected" ? "1 Online" : "0 Connected"}
          subValue="Authorized API feeds"
          icon={Network}
          badge="Live"
          badgeType={health?.services.mongodb.status === "connected" ? "success" : "neutral"}
        />
        <StatCard
          title="Data Sources Available"
          value="4 Connectors"
          subValue="1xBet, Spribe, BC, Aviator"
          icon={Database}
          badge="Ready"
          badgeType="neutral"
        />
        <StatCard
          title="Latest Verified Round"
          value="Standby"
          subValue="Awaiting live feed"
          icon={History}
          badge="Syncing"
          badgeType="warning"
        />
        <StatCard
          title="Model Validation"
          value="Baseline"
          subValue="Statistical Benchmark v1"
          icon={CheckCircle2}
          badge="Pass"
          badgeType="success"
        />
        <StatCard
          title="Paper Trading Balance"
          value="$10,000.00"
          subValue="Simulation Session"
          icon={Wallet}
          badge="Virtual"
          badgeType="neutral"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Multiplier Frequency Distribution"
          subtitle="Empirical density of observed round multiplier outcomes"
        >
          <EmptyState
            title="No Ingested Round Data"
            description="Empirical distribution charts render dynamically once telemetry is streamed or imported from an authorized platform."
            actionLabel="Configure Platform Connector"
            onAction={() => (window.location.href = "/platforms")}
            icon="database"
          />
        </ChartCard>

        <ChartCard
          title="Historical Multiplier Trend (Time Series)"
          subtitle="Sequential multiplier crash values over selected time window"
        >
          <EmptyState
            title="Telemetry Stream Disconnected"
            description="Awaiting live connection to real-time multiplier ingest pipelines."
            actionLabel="Open Live Monitor"
            onAction={() => (window.location.href = "/live-monitor")}
            icon="server"
          />
        </ChartCard>
      </div>

      {/* Secondary Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard
          title="Outcome Category Partition"
          subtitle="Proportions across standard volatility bins (e.g. 1.0x-1.5x, 2.0x-5.0x)"
        >
          <EmptyState
            title="Awaiting Data Partitioning"
            description="Minimum 100 verified rounds required to compute canonical histogram bins."
            icon="database"
          />
        </ChartCard>

        <ChartCard
          title="Data Ingestion Activity"
          subtitle="Telemetry event throughput and socket latency"
        >
          <div className="p-4 rounded-lg bg-surface-muted/40 border border-border/40 space-y-3">
            <div className="flex justify-between text-xs">
              <span className="text-muted">FastAPI Gateway</span>
              <span className="font-semibold text-emerald-400">Online (&lt; 2ms)</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted">MongoDB Atlas Storage</span>
              <span className="font-semibold text-blue-400">
                {health?.services.mongodb.status || "Unconfigured"}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted">Redis State Bus</span>
              <span className="font-semibold text-purple-400">
                {health?.services.redis.status || "Disconnected"}
              </span>
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Model Validation Status"
          subtitle="Walk-forward predictive edge & calibration benchmarks"
        >
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
            <AlertTriangle className="w-8 h-8 text-amber-400" />
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
              No Predictive Edge Injected
            </h4>
            <p className="text-[11px] text-muted">
              Models remain strictly uncalibrated until genuine historical telemetry datasets are validated against randomness baselines.
            </p>
          </div>
        </ChartCard>
      </div>

      {/* Recent System & Telemetry Events */}
      <div className="glass-panel p-5 rounded-xl border border-border">
        <div className="flex items-center justify-between pb-3 border-b border-border/60 mb-4">
          <h3 className="text-sm font-bold text-foreground">Recent Telemetry & Audit Events</h3>
          <span className="text-xs text-muted">Real-Time Event Stream</span>
        </div>
        <div className="divide-y divide-border/40">
          <div className="py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="font-semibold text-foreground">FastAPI Gateway Initialized</span>
              <span className="text-muted text-[11px] hidden sm:inline">Version 1.0.0 mounted at /api/v1</span>
            </div>
            <span className="text-muted text-[11px] font-mono">System Core</span>
          </div>
          <div className="py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span className="font-semibold text-foreground">Platform Connectors Standby</span>
              <span className="text-muted text-[11px] hidden sm:inline">Awaiting authorized API keys / telemetry URLs</span>
            </div>
            <span className="text-muted text-[11px] font-mono">Gateway Ingest</span>
          </div>
          <div className="py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              <span className="font-semibold text-foreground">Next.js 15 Client Active</span>
              <span className="text-muted text-[11px] hidden sm:inline">TypeScript App Router & analytical design tokens loaded</span>
            </div>
            <span className="text-muted text-[11px] font-mono">Frontend</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

