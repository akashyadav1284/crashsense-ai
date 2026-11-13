"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { ChartCard } from "@/components/ui/ChartCard";
import { StatCard } from "@/components/ui/StatCard";
import { EmptyState } from "@/components/ui/EmptyState";
import {
  BarChart3,
  TrendingUp,
  Percent,
  Sigma,
  Activity,
  Layers,
  Info,
} from "lucide-react";

export default function MultiplierAnalyticsPage() {
  const [selectedRange, setSelectedRange] = useState("all");

  return (
    <AppShell>
      <PageHeader
        title="Multiplier Analytics & Frequency Laboratory"
        description="Empirical distribution modeling, rolling statistical moments, and volatility partitioning. Historical frequencies must never be interpreted as next-round certainties."
        breadcrumbs={[{ label: "Analytics" }, { label: "Multiplier Analytics" }]}
        action={
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Category Filter:</span>
            <select
              value={selectedRange}
              onChange={(e) => setSelectedRange(e.target.value)}
              className="bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="all">All Multiplier Bands</option>
              <option value="1.0-1.49">1.00x – 1.49x</option>
              <option value="1.5-1.99">1.50x – 1.99x</option>
              <option value="2.0-4.99">2.00x – 4.99x</option>
              <option value="5.0-9.99">5.00x – 9.99x</option>
              <option value="10.0-19.99">10.00x – 19.99x</option>
              <option value="20.0+">20.00x+</option>
            </select>
          </div>
        }
      />

      {/* Disclaimers & Methodology Banner */}
      <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 flex items-start gap-3 text-xs text-muted">
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-foreground">Statistical Integrity Principle: </span>
          Independent Provably Fair crash rounds are memoryless Bernoulli-type random processes. Observed historical empirical density maps past occurrences and never constitutes a predictive guarantee for future outcomes.
        </div>
      </div>

      {/* Statistical Summary Metrics (Moment Statistics) */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <StatCard title="Total Samples (N)" value="0" subValue="Awaiting Ingest" icon={Layers} />
        <StatCard title="Mean (μ)" value="N/A" subValue="Empirical average" icon={Sigma} />
        <StatCard title="Median" value="N/A" subValue="50th Percentile" icon={Percent} />
        <StatCard title="Minimum" value="N/A" subValue="Lowest recorded" icon={Activity} />
        <StatCard title="Maximum" value="N/A" subValue="Peak multiplier" icon={TrendingUp} />
        <StatCard title="Variance (σ²)" value="N/A" subValue="Dispersion" icon={Sigma} />
        <StatCard title="Std Dev (σ)" value="N/A" subValue="Volatility" icon={BarChart3} />
      </div>

      {/* Primary Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Multiplier Histogram (Empirical Density)"
          subtitle="Frequency distribution across discretized multiplier bins"
        >
          <EmptyState
            title="Insufficient Sample Size (N = 0)"
            description="A minimum dataset of verified historical crash rounds is required to compute empirical probability densities."
            actionLabel="Go to Historical Rounds"
            onAction={() => (window.location.href = "/historical-rounds")}
            icon="database"
          />
        </ChartCard>

        <ChartCard
          title="Cumulative Distribution Function (CDF)"
          subtitle="Empirical probability P(Crash <= x) plotted against theoretical curves"
        >
          <EmptyState
            title="No CDF Data Available"
            description="Cumulative distribution computations require continuous sequential round telemetry."
            icon="database"
          />
        </ChartCard>

        <ChartCard
          title="Rolling Average & Median (Window: 50)"
          subtitle="Sequential trend smoothing over sequential round events"
        >
          <EmptyState
            title="Rolling Series Inactive"
            description="Requires an active time-series dataset with at least 50 continuous rounds."
            icon="server"
          />
        </ChartCard>

        <ChartCard
          title="Rolling Volatility & Standard Deviation"
          subtitle="Dynamic dispersion tracking across historical intervals"
        >
          <EmptyState
            title="Volatility Signal Inactive"
            description="Awaiting historical variance telemetry."
            icon="server"
          />
        </ChartCard>

        <ChartCard
          title="Quantile & Percentile Spectrum"
          subtitle="Observed 10th, 25th, 50th, 75th, 90th, and 99th percentiles"
        >
          <EmptyState
            title="Quantile Computation Idle"
            description="Requires sample population before computing rank percentiles."
            icon="database"
          />
        </ChartCard>

        <ChartCard
          title="Cross-Platform Distribution Comparison"
          subtitle="Side-by-side empirical divergence across monitored platforms"
        >
          <EmptyState
            title="Platform Comparison Standby"
            description="Requires at least 2 active connected platform streams."
            actionLabel="Connect Platforms"
            onAction={() => (window.location.href = "/platforms")}
            icon="server"
          />
        </ChartCard>
      </div>
    </AppShell>
  );
}

