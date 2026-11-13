"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  BrainCircuit,
  Sliders,
  AlertTriangle,
  Play,
  BarChart3,
  FileCheck,
  CheckCircle2,
  XCircle,
  TrendingDown,
  Layers,
  ShieldCheck,
  RefreshCw,
  GitCompare,
} from "lucide-react";

export default function MLLabPage() {
  const [models, setModels] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [training, setTraining] = useState<boolean>(false);
  const [trainStatusMsg, setTrainStatusMsg] = useState<string>("");

  // Training form state
  const [algorithm, setAlgorithm] = useState<string>("RANDOM_FOREST");
  const [targetThreshold, setTargetThreshold] = useState<number>(2.0);
  const [splits, setSplits] = useState<number>(4);
  const [windowSize, setWindowSize] = useState<number>(25);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [fetchedModels, fetchedExperiments] = await Promise.all([
        api.getMLModels().catch(() => []),
        api.getMLExperiments().catch(() => []),
      ]);
      setModels(fetchedModels);
      setExperiments(fetchedExperiments);
      if (fetchedModels.length > 0 && !selectedModel) {
        setSelectedModel(fetchedModels[0]);
      }
    } catch (err) {
      console.error("Error fetching ML registry data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    setTraining(true);
    setTrainStatusMsg("Executing walk-forward cross-validation on chronological data...");
    try {
      const payload = {
        experiment_name: `${algorithm} @ ${targetThreshold}x WF-Exp`,
        algorithm,
        platform_id: "1xbet",
        game_provider: "spribe",
        game_id: "aviator",
        room_id: "standard",
        target_threshold: Number(targetThreshold),
        walk_forward_splits: Number(splits),
        feature_window_size: Number(windowSize),
        hyperparameters:
          algorithm === "RANDOM_FOREST"
            ? { n_estimators: 30, max_depth: 4 }
            : algorithm === "XGBOOST"
            ? { n_estimators: 30, max_depth: 3 }
            : { C: 1.0 },
      };

      const result = await api.trainMLModel(payload);
      setTrainStatusMsg(`Training complete! Edge status: ${result.has_validated_edge ? "VALIDATED" : "REJECTED"}`);
      await fetchData();
    } catch (err: any) {
      setTrainStatusMsg(`Training error: ${err.message || "Failed to train model"}`);
    } finally {
      setTraining(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Machine Learning Research Laboratory"
          description="Model training, walk-forward chronological validation, calibration curves, and statistical baseline verification."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Analytics", href: "/analytics" },
            { label: "ML Laboratory" },
          ]}
          action={
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#263247] text-xs text-slate-300 hover:bg-[#111827] transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Registry
            </button>
          }
        />

        {/* SCIENTIFIC MANDATE BANNER */}
        <div className="p-4 rounded-xl border border-purple-500/30 bg-purple-950/20 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-purple-400 mt-0.5 shrink-0" />
          <div className="text-xs space-y-1 text-slate-300">
            <span className="font-semibold text-purple-300">Scientific Integrity & Zero-Leakage Policy:</span>
            <p className="text-slate-400">
              Models are benchmarked against <strong>Null CSPRNG Independence</strong> and <strong>Historical Frequency</strong> baselines. Walk-forward validation uses expanding chronological windows without temporal shuffling. Models failing to beat the Brier score of independent random sequences are strictly rejected.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* TRAINING LAUNCHER PANEL */}
          <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
            <div className="flex items-center gap-2 text-slate-100 font-semibold text-sm">
              <Sliders className="w-4 h-4 text-purple-400" />
              <span>Train Candidate Model</span>
            </div>

            <form onSubmit={handleTrain} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Algorithm</label>
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-purple-500"
                >
                  <option value="RANDOM_FOREST">Random Forest Classifier</option>
                  <option value="XGBOOST">XGBoost Classifier</option>
                  <option value="LOGISTIC_REGRESSION">Logistic Regression (L2)</option>
                  <option value="HIST_GRADIENT_BOOSTING">HistGradientBoosting</option>
                  <option value="BASELINE_FREQUENCY">Historical Frequency (Baseline)</option>
                  <option value="NULL_INDEPENDENCE">Null CSPRNG (Baseline)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Target Threshold (Multiplier)</label>
                <select
                  value={targetThreshold}
                  onChange={(e) => setTargetThreshold(Number(e.target.value))}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-purple-500"
                >
                  <option value={1.5}>1.50x (Moderate Bust Target)</option>
                  <option value={2.0}>2.00x (Standard Target)</option>
                  <option value={3.0}>3.00x (High Risk Target)</option>
                  <option value={5.0}>5.00x (Rare Surge Target)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Walk-Forward Folds</label>
                  <input
                    type="number"
                    min={2}
                    max={8}
                    value={splits}
                    onChange={(e) => setSplits(Number(e.target.value))}
                    className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">History Window</label>
                  <input
                    type="number"
                    min={15}
                    max={100}
                    value={windowSize}
                    onChange={(e) => setWindowSize(Number(e.target.value))}
                    className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={training}
                className="w-full mt-2 flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium transition"
              >
                {training ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Training...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" /> Run Walk-Forward Experiment
                  </>
                )}
              </button>

              {trainStatusMsg && (
                <div className="p-2.5 rounded-lg bg-[#0D1220] border border-[#263247] text-slate-300 text-[11px] leading-relaxed">
                  {trainStatusMsg}
                </div>
              )}
            </form>
          </div>

          {/* MODEL REGISTRY LIST */}
          <div className="lg:col-span-2 rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-100 font-semibold text-sm">
                <BrainCircuit className="w-4 h-4 text-purple-400" />
                <span>Model Registry & Lifecycle States</span>
              </div>
              <span className="text-xs text-slate-400">{models.length} Registered</span>
            </div>

            {loading ? (
              <div className="py-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-purple-400" /> Loading registry...
              </div>
            ) : models.length === 0 ? (
              <div className="py-10 text-center text-slate-500 text-xs">
                No trained models in registry. Launch a walk-forward experiment to register candidate models.
              </div>
            ) : (
              <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                {models.map((m) => {
                  const isSelected = selectedModel?.model_id === m.model_id;
                  return (
                    <div
                      key={m.model_id}
                      onClick={() => setSelectedModel(m)}
                      className={`p-3 rounded-lg border transition cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "border-purple-500 bg-purple-950/20"
                          : "border-[#263247] bg-[#0D1220] hover:border-slate-600"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-xs text-slate-200">{m.name}</span>
                          <span className="text-[10px] text-slate-400 font-mono">[{m.algorithm}]</span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-3">
                          <span>Target: {m.target_threshold}x</span>
                          <span>Brier: {m.evaluation_metrics?.brier_score?.toFixed(4) || "N/A"}</span>
                          <span>AUC: {m.evaluation_metrics?.roc_auc?.toFixed(4) || "N/A"}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {m.has_validated_edge ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> EDGE
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/40 text-rose-400 border border-rose-500/30 flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> NO EDGE
                          </span>
                        )}
                        <StatusBadge
                          status={m.status === "VALIDATED" ? "VERIFIED" : m.status === "REJECTED" ? "REJECTED" : "STANDBY"}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* SELECTED MODEL DETAILED INSPECTION */}
        {selectedModel && (
          <div className="rounded-xl border border-[#263247] bg-[#111827] p-6 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#263247] pb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <span>{selectedModel.name}</span>
                  <span className="text-xs font-mono text-purple-400 font-normal">({selectedModel.model_id})</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Evaluated on {selectedModel.training_sample_count} chronological historical rounds with zero future leakage.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-mono">Status:</span>
                <span
                  className={`px-2.5 py-1 rounded text-xs font-semibold uppercase ${
                    selectedModel.status === "VALIDATED"
                      ? "bg-emerald-950/50 text-emerald-400 border border-emerald-500/40"
                      : "bg-rose-950/50 text-rose-400 border border-rose-500/40"
                  }`}
                >
                  {selectedModel.status}
                </span>
              </div>
            </div>

            {/* METRICS COMPARISON GRID */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                <span className="text-[11px] text-slate-400">Out-of-Sample Brier Score</span>
                <div className="text-lg font-bold text-slate-100 mt-1">
                  {selectedModel.evaluation_metrics?.brier_score?.toFixed(4) || "N/A"}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Null Baseline: {selectedModel.baseline_metrics?.brier_score?.toFixed(4) || "0.2500"}
                </div>
              </div>

              <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                <span className="text-[11px] text-slate-400">Out-of-Sample Log Loss</span>
                <div className="text-lg font-bold text-slate-100 mt-1">
                  {selectedModel.evaluation_metrics?.log_loss?.toFixed(4) || "N/A"}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Null Baseline: {selectedModel.baseline_metrics?.log_loss?.toFixed(4) || "0.6931"}
                </div>
              </div>

              <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                <span className="text-[11px] text-slate-400">ROC AUC</span>
                <div className="text-lg font-bold text-slate-100 mt-1">
                  {selectedModel.evaluation_metrics?.roc_auc?.toFixed(4) || "N/A"}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Theoretical Random: 0.5000</div>
              </div>

              <div className="p-3.5 rounded-lg border border-[#263247] bg-[#0D1220]">
                <span className="text-[11px] text-slate-400">Expected Calibration Error (ECE)</span>
                <div className="text-lg font-bold text-slate-100 mt-1">
                  {selectedModel.evaluation_metrics?.expected_calibration_error?.toFixed(4) || "N/A"}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">10-Bin Reliability Error</div>
              </div>
            </div>

            {/* EDGE VERIFICATION NOTES */}
            <div className="p-4 rounded-xl border border-[#263247] bg-[#0D1220] space-y-2">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-purple-400" /> Statistical Edge Verification Findings:
              </span>
              <p className="text-xs text-slate-300 font-mono leading-relaxed">
                {selectedModel.edge_validation_notes || "No validation notes recorded."}
              </p>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
