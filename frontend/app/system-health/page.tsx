"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import { HealthState } from "@/types";
import {
  HeartPulse,
  Database,
  Radio,
  Server,
  Cpu,
  RefreshCw,
  Clock,
  ShieldCheck,
} from "lucide-react";

export default function SystemHealthPage() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = () => {
    setLoading(true);
    api
      .getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Infrastructure & Subsystem Diagnostics"
        description="Live operational telemetry covering the Next.js client, FastAPI async microservice, MongoDB Atlas cluster connection, and Redis event stream."
        breadcrumbs={[{ label: "System" }, { label: "System Health" }]}
        action={
          <button
            onClick={fetchStatus}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Diagnostics
          </button>
        }
      />

      {/* Aggregate Health Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Health"
          value={health?.status.toUpperCase() || "CHECKING"}
          subValue="Gateway Status"
          icon={HeartPulse}
          badge={health?.status === "healthy" ? "All Clear" : "Degraded"}
          badgeType={health?.status === "healthy" ? "success" : "warning"}
        />
        <StatCard
          title="API Gateway Latency"
          value="< 4ms"
          subValue="FastAPI async event loop"
          icon={Server}
          badge="Optimal"
          badgeType="success"
        />
        <StatCard
          title="MongoDB Atlas Pool"
          value={health?.services.mongodb.status.toUpperCase() || "STANDBY"}
          subValue={health?.services.mongodb.message || "Awaiting credentials"}
          icon={Database}
          badge={health?.services.mongodb.status === "connected" ? "Live" : "Unverified"}
          badgeType={health?.services.mongodb.status === "connected" ? "success" : "neutral"}
        />
        <StatCard
          title="Redis State Cache"
          value={health?.services.redis.status.toUpperCase() || "DISCONNECTED"}
          subValue={health?.services.redis.message || "Cache bus standby"}
          icon={Radio}
          badge={health?.services.redis.status === "connected" ? "Live" : "Standby"}
          badgeType={health?.services.redis.status === "connected" ? "success" : "neutral"}
        />
      </div>

      {/* Detailed Component Breakdown */}
      <div className="glass-panel rounded-xl border border-border overflow-hidden">
        <div className="p-4 border-b border-border/60 flex items-center justify-between">
          <h3 className="text-sm font-bold text-foreground">Subsystem Component Manifest</h3>
          <span className="text-xs text-muted font-mono">{health?.timestamp || "Active"}</span>
        </div>

        <div className="divide-y divide-border/40 text-xs">
          {/* Frontend */}
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-3">
              <Cpu className="w-5 h-5 text-primary" />
              <div>
                <p className="font-bold text-foreground">Next.js 15 Client Tier</p>
                <p className="text-[11px] text-muted">React 19 App Router with TypeScript Strict Mode</p>
              </div>
            </div>
            <StatusBadge status="ACTIVE" />
          </div>

          {/* FastAPI Core */}
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-3">
              <Server className="w-5 h-5 text-emerald-400" />
              <div>
                <p className="font-bold text-foreground">FastAPI Telemetry Gateway</p>
                <p className="text-[11px] text-muted">
                  Mounted at <code>{health?.app_name || "CrashSense AI Backend"}</code> v{health?.version || "1.0.0"} ({health?.environment || "development"})
                </p>
              </div>
            </div>
            <StatusBadge status={health ? "HEALTHY" : "DEGRADED"} />
          </div>

          {/* MongoDB Atlas */}
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-3">
              <Database className="w-5 h-5 text-blue-400" />
              <div>
                <p className="font-bold text-foreground">MongoDB Atlas Persistence Layer</p>
                <p className="text-[11px] text-muted">
                  Database: <code>{health?.services.mongodb.database || "crashsense"}</code> • Motor Async IO Driver
                </p>
              </div>
            </div>
            <StatusBadge status={health?.services.mongodb.status || "UNCONFIGURED"} />
          </div>

          {/* Redis */}
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-3">
              <Radio className="w-5 h-5 text-purple-400" />
              <div>
                <p className="font-bold text-foreground">Redis Real-Time PubSub & In-Memory Bus</p>
                <p className="text-[11px] text-muted">aioredis async connection manager</p>
              </div>
            </div>
            <StatusBadge status={health?.services.redis.status || "DISCONNECTED"} />
          </div>

          {/* Background Ingest Worker */}
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center space-x-3">
              <Clock className="w-5 h-5 text-amber-400" />
              <div>
                <p className="font-bold text-foreground">Telemetry Ingest Daemon</p>
                <p className="text-[11px] text-muted">Awaiting platform stream authorization</p>
              </div>
            </div>
            <StatusBadge status="STANDBY" />
          </div>
        </div>
      </div>
    </AppShell>
  );
}

