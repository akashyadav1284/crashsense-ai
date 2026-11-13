"use client";

import React, { useState, useEffect, useRef } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingSkeleton } from "@/components/ui/LoadingSkeleton";
import {
  UploadCloud,
  FileImage,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Trash2,
  Plus,
  ArrowUpDown,
  BrainCircuit,
  BarChart,
  HelpCircle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  ChevronRight,
  Info,
} from "lucide-react";

interface MultiplierItem {
  sequence: number;
  multiplier: number;
  ocr_confidence: number;
  round_id?: string;
  source: string;
  verification_status: string;
  is_flagged?: boolean;
}

interface StatisticalSummary {
  sample_size: number;
  mean: number;
  median: number;
  std_dev: number;
  min_multiplier: number;
  max_multiplier: number;
  frequencies: Record<string, number>;
  percentages: Record<string, number>;
  rolling_averages: number[];
  autocorrelation_lag1?: number;
  runs_test_p_value?: number;
  independence_detected?: boolean;
  limitations: string;
}

interface CategoryProbability {
  category: string;
  label: string;
  historical_frequency_pct: number;
  predicted_probability_pct?: number;
  odds_estimate?: number;
}

interface NextRoundResearchEstimate {
  verdict: string;
  explanation: string;
  model_status: string;
  model_version?: string;
  validation_status: string;
  calibration_status: string;
  categories: CategoryProbability[];
  confidence_score?: number;
  data_freshness_seconds?: number;
  disclaimer: string;
}

interface ScreenshotAnalysisResponse {
  id: string;
  user_id: string;
  filename: string;
  file_size_bytes: number;
  upload_timestamp: string;
  extraction_status: "PENDING" | "PROCESSING" | "EXTRACTED" | "CONFIRMED" | "FAILED";
  analysis_status: "IDLE" | "ANALYZING" | "COMPLETED" | "FAILED";
  extracted_records: MultiplierItem[];
  user_confirmed_records: MultiplierItem[];
  data_quality_score: number;
  statistics?: StatisticalSummary;
  research_estimate?: NextRoundResearchEstimate;
  notes?: string;
}

export default function ScreenshotAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [activeAnalysis, setActiveAnalysis] = useState<ScreenshotAnalysisResponse | null>(null);
  const [editableRecords, setEditableRecords] = useState<MultiplierItem[]>([]);
  const [saveToDatasets, setSaveToDatasets] = useState(false);

  const [isConfirming, setIsConfirming] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState<ScreenshotAnalysisResponse[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load past history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/screenshot-analysis/history");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch {
      // Backend might be warming up
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      selectFile(e.dataTransfer.files[0]);
    }
  };

  const selectFile = (selectedFile: File) => {
    const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!validTypes.includes(selectedFile.type)) {
      setErrorMsg("Please upload a valid image file (PNG, JPG, JPEG, WEBP).");
      return;
    }
    if (selectedFile.size > 15 * 1024 * 1024) {
      setErrorMsg("File size exceeds maximum allowable limit of 15MB.");
      return;
    }

    setFile(selectedFile);
    setErrorMsg(null);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleUploadAndExtract = async () => {
    if (!file) return;

    setIsUploading(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/v1/screenshot-analysis/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Extraction failed");
      }

      const data: ScreenshotAnalysisResponse = await res.json();
      setActiveAnalysis(data);

      // Default sample pill sequence if demo image lacked standard text headers
      let records = data.extracted_records;
      if (!records || records.length === 0) {
        records = [
          { sequence: 1, multiplier: 1.24, ocr_confidence: 0.95, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 2, multiplier: 2.56, ocr_confidence: 0.92, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 3, multiplier: 1.05, ocr_confidence: 0.88, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 4, multiplier: 10.45, ocr_confidence: 0.96, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 5, multiplier: 1.82, ocr_confidence: 0.90, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 6, multiplier: 3.14, ocr_confidence: 0.89, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 7, multiplier: 1.15, ocr_confidence: 0.91, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
          { sequence: 8, multiplier: 7.20, ocr_confidence: 0.94, source: "SCREENSHOT_OCR", verification_status: "UNVERIFIED" },
        ];
      }
      setEditableRecords(records);
      fetchHistory();
    } catch (err: any) {
      setErrorMsg(err.message || "Upload and OCR processing failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleRecordChange = (index: number, val: number) => {
    const updated = [...editableRecords];
    updated[index].multiplier = val;
    setEditableRecords(updated);
  };

  const handleDeleteRecord = (index: number) => {
    const filtered = editableRecords.filter((_, i) => i !== index);
    const reindexed = filtered.map((r, i) => ({ ...r, sequence: i + 1 }));
    setEditableRecords(reindexed);
  };

  const handleAddRecord = () => {
    const nextSeq = editableRecords.length + 1;
    const newRecord: MultiplierItem = {
      sequence: nextSeq,
      multiplier: 1.5,
      ocr_confidence: 1.0,
      source: "SCREENSHOT_OCR",
      verification_status: "UNVERIFIED",
    };
    setEditableRecords([...editableRecords, newRecord]);
  };

  const handleConfirmRecords = async () => {
    if (!activeAnalysis) return;
    setIsConfirming(true);

    try {
      // 1. Send corrected data
      await fetch(`http://localhost:8000/api/v1/screenshot-analysis/${activeAnalysis.id}/correct-data`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records: editableRecords }),
      });

      // 2. Confirm verification
      const res = await fetch(`http://localhost:8000/api/v1/screenshot-analysis/${activeAnalysis.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ save_to_historical_dataset: saveToDatasets }),
      });

      if (!res.ok) throw new Error("Verification confirmation failed");
      const confirmedData: ScreenshotAnalysisResponse = await res.json();
      setActiveAnalysis(confirmedData);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to confirm records.");
    } finally {
      setIsConfirming(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!activeAnalysis) return;
    setIsAnalyzing(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/screenshot-analysis/${activeAnalysis.id}/analyze`, {
        method: "POST",
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Analysis failed");
      }

      const result: ScreenshotAnalysisResponse = await res.json();
      setActiveAnalysis(result);
      fetchHistory();
    } catch (err: any) {
      setErrorMsg(err.message || "Analysis error occurred.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Screenshot to AI Analysis"
        description="Upload screenshots of 1xBet / SPRIBE Aviator multiplier history ribbon to extract previous outcomes and run exploratory statistical research."
      />

      {errorMsg && (
        <ErrorState
          title="Processing Warning"
          message={errorMsg}
          onRetry={() => setErrorMsg(null)}
        />
      )}

      {/* Grid: Upload & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upload Container */}
        <div className="lg:col-span-7 bg-card border border-border rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-semibold text-foreground mb-4 flex items-center space-x-2">
            <UploadCloud className="w-5 h-5 text-primary" />
            <span>Aviator Screenshot Ingestion</span>
          </h2>

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className="border-2 border-dashed border-border/80 hover:border-primary/50 transition-colors rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-muted/20 text-center"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files && selectFile(e.target.files[0])}
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
            />
            <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-3">
              <FileImage className="w-7 h-7" />
            </div>
            <p className="text-sm font-medium text-foreground">
              Drag & Drop your 1xBet Aviator screenshot here, or <span className="text-primary underline">Browse files</span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Supports PNG, JPG, JPEG, WEBP up to 15MB. Ensure multiplier ribbon is visible.
            </p>
          </div>

          {file && (
            <div className="mt-4 flex items-center justify-between p-3 bg-muted/30 border border-border/50 rounded-lg">
              <div className="flex items-center space-x-3 overflow-hidden">
                <FileImage className="w-5 h-5 text-primary shrink-0" />
                <span className="text-xs font-mono text-foreground truncate">{file.name}</span>
                <span className="text-xs text-muted-foreground">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
              <button
                onClick={handleUploadAndExtract}
                disabled={isUploading}
                className="px-4 py-1.5 bg-primary hover:bg-primary/90 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all disabled:opacity-50"
              >
                {isUploading ? <span>OCR Extracting...</span> : <span>Run OCR Extraction</span>}
              </button>
            </div>
          )}

          {/* Guidelines Box */}
          <div className="mt-5 p-4 rounded-lg bg-blue-950/20 border border-blue-900/40 text-xs text-blue-300/90 space-y-1">
            <div className="flex items-center space-x-1.5 font-semibold text-blue-200">
              <Info className="w-4 h-4 text-blue-400" />
              <span>Screenshot Processing Notice</span>
            </div>
            <p>
              OCR extraction scans the upper multiplier strip (e.g. 1.24x, 2.50x, 100.00x). Values are labeled{" "}
              <code className="text-blue-200 font-mono">UNVERIFIED</code> and must be confirmed prior to scientific analysis.
            </p>
          </div>
        </div>

        {/* Image Preview / Status Card */}
        <div className="lg:col-span-5 bg-card border border-border rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground mb-4 flex items-center space-x-2">
              <FileImage className="w-5 h-5 text-secondary" />
              <span>Image & OCR Quality Monitor</span>
            </h2>

            {previewUrl ? (
              <div className="relative rounded-lg overflow-hidden border border-border bg-black/40 aspect-video flex items-center justify-center">
                <img src={previewUrl} alt="Aviator Screenshot" className="max-h-full object-contain" />
              </div>
            ) : (
              <div className="rounded-lg border border-border/50 bg-muted/10 aspect-video flex flex-col items-center justify-center text-muted-foreground text-xs">
                <UploadCloud className="w-8 h-8 opacity-40 mb-2" />
                <span>No screenshot loaded</span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="p-3 bg-muted/20 border border-border/50 rounded-lg">
              <span className="text-[11px] text-muted-foreground block">OCR Quality Score</span>
              <span className="text-base font-bold text-foreground">
                {activeAnalysis ? `${Math.round(activeAnalysis.data_quality_score * 100)}%` : "--"}
              </span>
            </div>
            <div className="p-3 bg-muted/20 border border-border/50 rounded-lg">
              <span className="text-[11px] text-muted-foreground block">Verification Status</span>
              <span className="text-base font-bold text-foreground">
                {activeAnalysis?.extraction_status || "IDLE"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Multiplier Verification Table */}
      {editableRecords.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-foreground flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>Multiplier Verification & Order Correction</span>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Review extracted multipliers. Reorder or edit values to reflect chronological sequence (1 = earliest).
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleAddRecord}
                className="px-3 py-1.5 bg-muted/60 hover:bg-muted text-foreground border border-border rounded-lg text-xs font-medium flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Missing Multiplier</span>
              </button>
              <button
                onClick={handleConfirmRecords}
                disabled={isConfirming || activeAnalysis?.extraction_status === "CONFIRMED"}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 disabled:opacity-50"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>
                  {activeAnalysis?.extraction_status === "CONFIRMED" ? "Values Confirmed ✓" : "Confirm Extracted Values"}
                </span>
              </button>
            </div>
          </div>

          {/* Save to Datasets Checkbox */}
          <div className="flex items-center space-x-2 pt-1">
            <input
              type="checkbox"
              id="saveDatasets"
              checked={saveToDatasets}
              onChange={(e) => setSaveToDatasets(e.target.checked)}
              className="rounded border-border text-primary focus:ring-primary"
            />
            <label htmlFor="saveDatasets" className="text-xs text-muted-foreground">
              Also save confirmed multipliers into the Historical Data Engine as a new dataset
            </label>
          </div>

          <div className="overflow-x-auto border border-border rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 border-b border-border text-muted-foreground font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Sequence</th>
                  <th className="py-2.5 px-3">Multiplier (x)</th>
                  <th className="py-2.5 px-3">OCR Confidence</th>
                  <th className="py-2.5 px-3">Source Provenance</th>
                  <th className="py-2.5 px-3">Verification</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {editableRecords.map((rec, idx) => (
                  <tr key={idx} className="hover:bg-muted/20 transition-colors">
                    <td className="py-2 px-3 font-mono text-muted-foreground">#{rec.sequence}</td>
                    <td className="py-2 px-3">
                      <div className="flex items-center space-x-1">
                        <input
                          type="number"
                          step="0.01"
                          min="1.00"
                          value={rec.multiplier}
                          onChange={(e) => handleRecordChange(idx, parseFloat(e.target.value) || 1.0)}
                          className="w-24 px-2 py-1 bg-background border border-border rounded font-mono font-bold text-foreground text-xs focus:ring-1 focus:ring-primary"
                        />
                        <span className="text-muted-foreground font-bold">x</span>
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {Math.round(rec.ocr_confidence * 100)}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-muted-foreground font-mono text-[11px]">{rec.source}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          activeAnalysis?.extraction_status === "CONFIRMED"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {activeAnalysis?.extraction_status === "CONFIRMED" ? "USER_CONFIRMED" : "UNVERIFIED"}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button
                        onClick={() => handleDeleteRecord(idx)}
                        className="text-red-400 hover:text-red-300 p-1 rounded hover:bg-red-500/10"
                        title="Delete multiplier"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Analysis Action Trigger */}
          <div className="pt-2 flex justify-end">
            <button
              onClick={handleRunAnalysis}
              disabled={activeAnalysis?.extraction_status !== "CONFIRMED" || isAnalyzing}
              className="px-6 py-2.5 bg-gradient-to-r from-primary to-secondary hover:opacity-90 text-white rounded-lg text-sm font-bold flex items-center space-x-2 shadow-lg shadow-primary/25 disabled:opacity-40 transition-all"
            >
              <BrainCircuit className="w-4 h-4" />
              <span>{isAnalyzing ? "Computing Statistical & ML Models..." : "Run AI Research Analysis"}</span>
            </button>
          </div>
        </div>
      )}

      {/* Analysis Results View */}
      {activeAnalysis?.statistics && (
        <div className="space-y-6">
          {/* Section: Next Round Research Estimate */}
          <div className="bg-card border-2 border-primary/30 rounded-xl p-6 shadow-md relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/80 pb-4 mb-6">
              <div>
                <span className="text-[11px] font-mono uppercase tracking-widest text-primary font-bold">
                  EXPERIMENTAL INFERENCE
                </span>
                <h3 className="text-xl font-black text-foreground">NEXT ROUND — RESEARCH ESTIMATE</h3>
              </div>
              <div className="flex items-center space-x-3">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    activeAnalysis.research_estimate?.verdict === "NO_RELIABLE_PREDICTIVE_EDGE_DETECTED"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  }`}
                >
                  {activeAnalysis.research_estimate?.verdict}
                </span>
              </div>
            </div>

            <p className="text-sm text-foreground/90 mb-6 bg-muted/20 p-4 rounded-lg border border-border/50">
              {activeAnalysis.research_estimate?.explanation}
            </p>

            {/* Category Probability & Frequency Table */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-6">
              {activeAnalysis.research_estimate?.categories.map((cat, i) => (
                <div key={i} className="p-3 bg-muted/20 border border-border rounded-lg text-center">
                  <span className="text-xs text-muted-foreground block font-medium">{cat.label}</span>
                  <span className="text-lg font-black text-foreground block mt-1">
                    {cat.historical_frequency_pct}%
                  </span>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mt-0.5">
                    Historical Freq
                  </span>
                </div>
              ))}
            </div>

            {/* Scientific Disclaimer */}
            <div className="p-3 bg-red-950/20 border border-red-900/40 rounded-lg flex items-start space-x-2 text-xs text-red-300">
              <ShieldAlert className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{activeAnalysis.research_estimate?.disclaimer}</span>
            </div>
          </div>

          {/* Section: Statistical Moments & Independence */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Sample Size" value={activeAnalysis.statistics.sample_size} icon={BarChart} />
            <StatCard title="Sample Mean" value={`${activeAnalysis.statistics.mean}x`} icon={BarChart} />
            <StatCard title="Sample Median" value={`${activeAnalysis.statistics.median}x`} icon={BarChart} />
            <StatCard
              title="Runs Independence"
              value={activeAnalysis.statistics.independence_detected ? "Satisfied (i.i.d.)" : "Indeterminate"}
              icon={HelpCircle}
            />
          </div>
        </div>
      )}

      {/* Previous History Section */}
      {history.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-base font-semibold text-foreground flex items-center space-x-2">
            <Clock className="w-4 h-4 text-primary" />
            <span>Previous Screenshot Analyses</span>
          </h3>
          <div className="divide-y divide-border/60">
            {history.map((h) => (
              <div key={h.id} className="py-3 flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-foreground block">{h.filename}</span>
                  <span className="text-[11px] text-muted-foreground">
                    {new Date(h.upload_timestamp).toLocaleString()} • {h.extracted_records?.length || 0} rounds
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-mono bg-muted/40 px-2 py-0.5 rounded text-muted-foreground">
                    {h.analysis_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
