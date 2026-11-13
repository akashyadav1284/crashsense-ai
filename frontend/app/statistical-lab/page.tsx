"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { ChartCard } from "@/components/ui/ChartCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { api } from "@/services/apiClient";
import {
  FlaskConical,
  BarChart3,
  TrendingUp,
  Percent,
  Sigma,
  Activity,
  Layers,
  Info,
  RefreshCw,
  GitCompare,
  Download,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

export default function StatisticalLabPage() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("ds-1xbet-aviator-standard");
  const [activeTab, setActiveTab] = useState<"overview" | "distribution" | "rolling" | "independence" | "drift" | "outliers">("overview");

  // Analytics states
  const [descStats, setDescStats] = useState<any>(null);
  const [distribution, setDistribution] = useState<any>(null);
  const [rollingStats, setRollingStats] = useState<any>(null);
  const [acfData, setAcfData] = useState<any>(null);
  const [driftData, setDriftData] = useState<any>(null);
  const [outlierData, setOutlierData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Load available datasets
  useEffect(() => {
    api.getDatasets().then((data) => {
      setDatasets(data);
      if (data.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(data[0].dataset_id);
      }
    });
  }, []);

  const loadAnalytics = () => {
    setLoading(true);
    Promise.all([
      api.getDescriptiveStats(selectedDatasetId).catch(() => null),
      api.getDistribution(selectedDatasetId).catch(() => null),
      api.getRollingStats(selectedDatasetId, 50).catch(() => null),
      api.getAutocorrelation(selectedDatasetId).catch(() => null),
      api.getDrift(selectedDatasetId).catch(() => null),
      api.getOutliers(selectedDatasetId).catch(() => null),
    ]).then(([desc, dist, roll, acf, drift, out]) => {
      setDescStats(desc);
      setDistribution(dist);
      setRollingStats(roll);
      setAcfData(acf);
      setDriftData(drift);
      setOutlierData(out);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadAnalytics();
  }, [selectedDatasetId]);

  return (
    <AppShell>
      <PageHeader
        title="Interactive Statistical Research Laboratory"
        description="Empirical distribution modeling, Ljung-Box autocorrelation hypothesis tests, Population Stability Index drift, and Wilson confidence bounds."
        breadcrumbs={[{ label: "Analytics" }, { label: "Statistical Laboratory" }]}
        action={
          <div className="flex items-center gap-3">
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-foreground font-semibold focus:outline-none focus:border-primary"
            >
              {datasets.map((d) => (
                <option key={d.dataset_id} value={d.dataset_id}>
                  {d.dataset_name} ({d.total_records} rounds)
                </option>
              ))}
            </select>
            <button
              onClick={loadAnalytics}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Recompute
            </button>
          </div>
        }
      />

      {/* Scientific Principle Banner */}
      <div className="p-3.5 rounded-xl bg-card border border-primary/30 flex items-start gap-3 text-xs text-muted">
        <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-foreground">Scientific Integrity Principle: </span>
          Provably Fair crash games are memoryless stochastic processes. Empirical distribution parameters describe historical sample observations and <strong>never imply forward-looking predictability or guaranteed returns</strong>.
        </div>
      </div>

      {/* Nav Tabs */}
      <div className="flex border-b border-border space-x-4 text-xs font-semibold">
        {[
          { key: "overview", label: "Overview & Moments" },
          { key: "distribution", label: "Distribution & Wilson CI" },
          { key: "rolling", label: "Rolling Statistics" },
          { key: "independence", label: "Independence & ACF" },
          { key: "drift", label: "Distribution Drift (KS/PSI)" },
          { key: "outliers", label: "Outlier Analysis" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`pb-2.5 transition border-b-2 ${
              activeTab === tab.key
                ? "border-primary text-primary font-bold"
                : "border-transparent text-muted hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            <StatCard
              title="Sample Size (N)"
              value={descStats?.sample_size || 0}
              subValue="Verified observations"
              icon={Layers}
            />
            <StatCard
              title="Sample Mean (μ)"
              value={descStats?.mean !== null && descStats?.mean !== undefined ? `${descStats.mean}x` : "N/A"}
              subValue="Empirical average"
              icon={Sigma}
            />
            <StatCard
              title="Median (P50)"
              value={descStats?.median !== null && descStats?.median !== undefined ? `${descStats.median}x` : "N/A"}
              subValue="50th Percentile"
              icon={Percent}
            />
            <StatCard
              title="Std Dev (σ)"
              value={descStats?.std_dev !== null && descStats?.std_dev !== undefined ? descStats.std_dev : "N/A"}
              subValue="Sample volatility"
              icon={Activity}
            />
            <StatCard
              title="Skewness"
              value={descStats?.skewness !== null && descStats?.skewness !== undefined ? descStats.skewness : "N/A"}
              subValue="Right-tail asymmetry"
              icon={TrendingUp}
            />
            <StatCard
              title="Kurtosis"
              value={descStats?.kurtosis !== null && descStats?.kurtosis !== undefined ? descStats.kurtosis : "N/A"}
              subValue="Tail thickness"
              icon={BarChart3}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard
              title="Quantile Spectrum (P1 - P99)"
              subtitle="Empirical percentiles across observed historical crash points"
            >
              {descStats && descStats.percentiles && Object.keys(descStats.percentiles).length > 0 ? (
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 p-4">
                  {Object.entries(descStats.percentiles).map(([k, v]) => (
                    <div key={k} className="p-3 rounded-lg bg-surface-muted/50 border border-border text-center">
                      <p className="text-[10px] text-muted font-bold">{k}</p>
                      <p className="text-base font-black text-foreground mt-0.5">{String(v)}x</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No Percentile Data"
                  description="Awaiting ingested historical records to compute quantile spectrum."
                  icon="database"
                />
              )}
            </ChartCard>

            <ChartCard
              title="Autocorrelation & Serial Memory Diagnostic"
              subtitle="Ljung-Box test for sequential dependence"
            >
              {acfData && acfData.ljung_box ? (
                <div className="p-4 space-y-3 text-xs">
                  <div className="flex justify-between border-b border-border/40 pb-2">
                    <span className="text-muted">Test:</span>
                    <span className="font-semibold text-foreground">{acfData.ljung_box.test_name}</span>
                  </div>
                  <div className="flex justify-between border-b border-border/40 pb-2">
                    <span className="text-muted">Ljung-Box Q Statistic:</span>
                    <span className="font-mono text-foreground">{acfData.ljung_box.test_statistic}</span>
                  </div>
                  <div className="flex justify-between border-b border-border/40 pb-2">
                    <span className="text-muted">p-value:</span>
                    <span className={`font-mono font-bold ${acfData.ljung_box.p_value < 0.05 ? "text-amber-400" : "text-emerald-400"}`}>
                      {acfData.ljung_box.p_value}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-border/40 pb-2">
                    <span className="text-muted">Null Hypothesis:</span>
                    <span className="text-muted text-[11px] text-right max-w-xs">{acfData.ljung_box.null_hypothesis}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-muted/40 border border-border/60 text-[11px] text-foreground">
                    <strong>Interpretation: </strong>
                    {acfData.ljung_box.interpretation}
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Independence Test Standby"
                  description="Requires at least 10 sequential round outcomes."
                  icon="server"
                />
              )}
            </ChartCard>
          </div>
        </div>
      )}

      {/* TAB 2: DISTRIBUTION */}
      {activeTab === "distribution" && (
        <div className="space-y-6">
          <div className="glass-panel rounded-xl border border-border overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-foreground">
                Multiplier Category Frequencies & 95% Wilson Confidence Intervals
              </h3>
              <span className="text-xs text-muted">
                Sample: {distribution?.sample_size || 0} rounds
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-muted/60 text-muted uppercase text-[10px] tracking-wider border-b border-border">
                  <tr>
                    <th className="py-3 px-4">Category Band</th>
                    <th className="py-3 px-4">Count (N)</th>
                    <th className="py-3 px-4">Empirical Frequency</th>
                    <th className="py-3 px-4">Cumulative Freq</th>
                    <th className="py-3 px-4">95% Wilson CI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-foreground font-mono">
                  {distribution?.categories && distribution.categories.length > 0 ? (
                    distribution.categories.map((c: any) => (
                      <tr key={c.category} className="hover:bg-surface-muted/30">
                        <td className="py-3 px-4 font-sans font-bold text-primary">{c.category}</td>
                        <td className="py-3 px-4">{c.count}</td>
                        <td className="py-3 px-4">{(c.relative_frequency * 100).toFixed(2)}%</td>
                        <td className="py-3 px-4 text-muted">{(c.cumulative_relative_frequency * 100).toFixed(2)}%</td>
                        <td className="py-3 px-4 text-emerald-400">
                          [{c.confidence_interval[0]}, {c.confidence_interval[1]}]
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted font-sans">
                        No distribution categories calculated yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: ROLLING */}
      {activeTab === "rolling" && (
        <ChartCard
          title="Rolling Statistical Series (Window: 50 Rounds)"
          subtitle="Sequential trend tracing without forward predictive implications"
        >
          {rollingStats && rollingStats.series && rollingStats.series.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-muted text-muted uppercase text-[10px]">
                  <tr>
                    <th className="py-2 px-3">Round ID</th>
                    <th className="py-2 px-3">Observed Multiplier</th>
                    <th className="py-2 px-3">Rolling Mean</th>
                    <th className="py-2 px-3">Rolling Median</th>
                    <th className="py-2 px-3">Rolling Volatility (σ)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {rollingStats.series.slice(-20).map((pt: any) => (
                    <tr key={pt.round_id} className="hover:bg-surface-muted/30">
                      <td className="py-2 px-3 text-primary">{pt.round_id}</td>
                      <td className="py-2 px-3 font-bold">{pt.observed_multiplier}x</td>
                      <td className="py-2 px-3">{pt.rolling_mean}x</td>
                      <td className="py-2 px-3">{pt.rolling_median}x</td>
                      <td className="py-2 px-3 text-muted">{pt.rolling_std}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="Rolling Window Standby"
              description="Requires at least 50 chronological rounds in the selected dataset."
              icon="server"
            />
          )}
        </ChartCard>
      )}

      {/* TAB 4: INDEPENDENCE */}
      {activeTab === "independence" && (
        <ChartCard
          title="Autocorrelation Function (ACF) - Lags 1 to 15"
          subtitle="Testing for serial dependence across consecutive rounds"
        >
          {acfData && acfData.lags && acfData.lags.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 p-4 font-mono text-xs">
              {acfData.lags.map((l: any) => (
                <div key={l.lag} className="p-3 rounded-lg bg-surface-muted/50 border border-border text-center">
                  <p className="text-[10px] text-muted font-sans font-bold">Lag {l.lag}</p>
                  <p className={`text-base font-black mt-0.5 ${l.statistically_significant ? "text-amber-400" : "text-foreground"}`}>
                    {l.autocorrelation}
                  </p>
                  <span className="text-[10px] text-muted font-sans">
                    Bound: ±{l.confidence_bound}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="ACF Calculations Standby"
              description="Ingest at least 10 rounds to compute lag correlations."
              icon="server"
            />
          )}
        </ChartCard>
      )}

      {/* TAB 5: DRIFT */}
      {activeTab === "drift" && (
        <ChartCard
          title="Distribution Drift & Population Stability Index (PSI)"
          subtitle="Two-Sample Kolmogorov-Smirnov test between sequential windows"
        >
          {driftData ? (
            <div className="p-4 space-y-3 text-xs">
              <div className="flex justify-between border-b border-border/40 pb-2">
                <span className="text-muted">Drift Status:</span>
                <span className="font-bold text-emerald-400">{driftData.drift_status}</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-2">
                <span className="text-muted">Population Stability Index (PSI):</span>
                <span className="font-mono text-foreground">{driftData.psi_score}</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-2">
                <span className="text-muted">Wasserstein Distance:</span>
                <span className="font-mono text-foreground">{driftData.wasserstein_distance}</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-2">
                <span className="text-muted">KS Statistic (D):</span>
                <span className="font-mono text-foreground">{driftData.ks_test?.test_statistic}</span>
              </div>
              <div className="flex justify-between border-b border-border/40 pb-2">
                <span className="text-muted">KS p-value:</span>
                <span className="font-mono text-foreground">{driftData.ks_test?.p_value}</span>
              </div>
              <p className="text-[11px] text-muted p-2 rounded bg-surface-muted/40 border border-border">
                {driftData.ks_test?.interpretation}
              </p>
            </div>
          ) : (
            <EmptyState
              title="Drift Evaluation Standby"
              description="Requires at least 20 sequential rounds to compare split windows."
              icon="server"
            />
          )}
        </ChartCard>
      )}

      {/* TAB 6: OUTLIERS */}
      {activeTab === "outliers" && (
        <ChartCard
          title="Statistical Outliers (Tukey 1.5x IQR Fences)"
          subtitle="Right-tail extreme multiplier events"
        >
          {outlierData && outlierData.outliers && outlierData.outliers.length > 0 ? (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-surface-muted/40 border border-border text-xs flex justify-between">
                <span>IQR Fence Upper Bound: <strong className="font-mono">{outlierData.iqr_bounds?.upper_bound}x</strong></span>
                <span>Total Outliers Identified: <strong className="font-mono">{outlierData.total_outliers}</strong></span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-surface-muted text-muted uppercase text-[10px]">
                    <tr>
                      <th className="py-2 px-3">Round ID</th>
                      <th className="py-2 px-3">Multiplier</th>
                      <th className="py-2 px-3">Detection Method</th>
                      <th className="py-2 px-3">Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {outlierData.outliers.map((o: any) => (
                      <tr key={o.round_id} className="hover:bg-surface-muted/30">
                        <td className="py-2 px-3 text-primary">{o.round_id}</td>
                        <td className="py-2 px-3 font-bold text-amber-400">{o.multiplier}x</td>
                        <td className="py-2 px-3 text-muted">{o.method}</td>
                        <td className="py-2 px-3 text-muted font-sans text-[11px]">{o.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <EmptyState
              title="No Statistical Outliers Identified"
              description="All observed multipliers fall within the 1.5x IQR upper fence."
              icon="database"
            />
          )}
        </ChartCard>
      )}
    </AppShell>
  );
}
