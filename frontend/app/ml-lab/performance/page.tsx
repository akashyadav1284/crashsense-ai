"use client";

import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { ChartCard } from "@/components/ui/ChartCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/ui/StatCard";
import {
  TrendingUp,
  Award,
  BarChart,
  Percent,
  CheckCircle,
} from "lucide-react";

export default function ModelPerformancePage() {
  return (
    <AppShell>
      <PageHeader
        title="Model Performance & Out-of-Sample Validation"
        description="Detailed calibration curves, reliability diagrams, log-loss progressions, and feature importance rankings."
        breadcrumbs={[
          { label: "Analytics" },
          { label: "ML Research Lab", href: "/ml-lab" },
          { label: "Model Performance" },
        ]}
      />

      {/* Model Benchmark KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Baseline Brier Score"
          value="0.250"
          subValue="Random baseline (Uniform)"
          icon={Award}
          badge="Benchmark"
          badgeType="neutral"
        />
        <StatCard
          title="Best Model Brier Score"
          value="N/A"
          subValue="Awaiting training run"
          icon={Percent}
          badge="Uncomputed"
          badgeType="neutral"
        />
        <StatCard
          title="Entropy / Log Loss"
          value="0.693"
          subValue="Theoretical memoryless limit"
          icon={BarChart}
          badge="Optimal"
          badgeType="success"
        />
        <StatCard
          title="Predictive Edge"
          value="0.00%"
          subValue="Indistinguishable from random"
          icon={TrendingUp}
          badge="Verified"
          badgeType="neutral"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Reliability Diagram (Calibration Curve)"
          subtitle="Estimated probabilities vs observed empirical frequencies"
        >
          <EmptyState
            title="Calibration Curve Standby"
            description="Generated after model validation against test partitions."
            icon="server"
          />
        </ChartCard>

        <ChartCard
          title="Feature Importance Ranking (MDI / Shapley)"
          subtitle="Relative contribution of rolling lag features and hash entropy"
        >
          <EmptyState
            title="No Features Computed"
            description="Feature importance matrix populates following model fit."
            icon="database"
          />
        </ChartCard>
      </div>
    </AppShell>
  );
}

