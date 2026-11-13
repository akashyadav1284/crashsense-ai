"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  Search,
  Download,
  Upload,
  RefreshCw,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  X,
  Layers,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Database,
  BarChart,
  Calendar,
} from "lucide-react";

export default function HistoricalRoundsPage() {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState("ds-1xbet-aviator-standard");
  const [roundsData, setRoundsData] = useState<any>({
    total_records: 0,
    page: 1,
    page_size: 50,
    total_pages: 1,
    rounds: [],
  });
  const [validationReport, setValidationReport] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  // Import modal
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importType, setImportType] = useState<"csv" | "json">("csv");
  const [importing, setImporting] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);

  // Load datasets list
  useEffect(() => {
    api
      .getDatasets()
      .then((data) => {
        setDatasets(data);
        if (data.length > 0 && !selectedDatasetId) {
          setSelectedDatasetId(data[0].dataset_id);
        }
      })
      .catch(() => setDatasets([]));
  }, []);

  // Fetch paginated rounds & validation report
  const fetchRoundsAndReport = () => {
    setLoading(true);
    api
      .getDatasetRounds(selectedDatasetId, {
        page: currentPage,
        pageSize: 50,
        sort: sortOrder,
        search: searchTerm,
      })
      .then((data) => setRoundsData(data))
      .catch(() =>
        setRoundsData({
          total_records: 0,
          page: 1,
          page_size: 50,
          total_pages: 1,
          rounds: [],
        })
      )
      .finally(() => setLoading(false));

    api
      .getDatasetValidationReport(selectedDatasetId)
      .then(setValidationReport)
      .catch(() => setValidationReport(null));
  };

  useEffect(() => {
    fetchRoundsAndReport();
  }, [selectedDatasetId, currentPage, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchRoundsAndReport();
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;

    setImporting(true);
    setImportStatus(null);
    const formData = new FormData();
    formData.append("file", importFile);
    formData.append("platform_id", "1xbet");
    formData.append("provider_id", "spribe");

    try {
      let res;
      if (importType === "csv") {
        res = await api.importCsv(formData);
      } else {
        res = await api.importJson(formData);
      }
      setImportStatus(
        `Import completed: ${res.accepted_records} accepted, ${res.duplicate_records} duplicates, ${res.rejected_records} rejected.`
      );
      fetchRoundsAndReport();
    } catch (err: any) {
      setImportStatus(`Import failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Historical Round Dataset Explorer"
        description="Audit, query, and filter genuine historical crash multiplier datasets (1,000+ records). Records maintain rigorous provenance and schema validation."
        breadcrumbs={[{ label: "Monitoring" }, { label: "Historical Rounds" }]}
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowImportModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-xs font-semibold text-white shadow-md shadow-primary/20 transition"
            >
              <Upload className="w-3.5 h-3.5" />
              Import Data File
            </button>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/datasets/${selectedDatasetId}/export/csv`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </a>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/datasets/${selectedDatasetId}/export/json`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
            >
              <Download className="w-3.5 h-3.5" />
              Export JSON
            </a>
          </div>
        }
      />

      {/* Dataset Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Records (N)"
          value={roundsData.total_records}
          subValue="Ingested canonical rounds"
          icon={Layers}
          badge="Audit"
          badgeType="neutral"
        />
        <StatCard
          title="Accepted Records"
          value={validationReport ? validationReport.valid_records : 0}
          subValue="Valid multiplier schema"
          icon={CheckCircle2}
          badge="Pass"
          badgeType="success"
        />
        <StatCard
          title="Duplicate Rounds"
          value={validationReport ? validationReport.duplicate_records : 0}
          subValue="Compound key collisions"
          icon={AlertCircle}
          badge="Ignored"
          badgeType="neutral"
        />
        <StatCard
          title="Rejected Records"
          value={validationReport ? validationReport.invalid_records : 0}
          subValue="Non-positive or malformed"
          icon={AlertCircle}
          badge="Filtered"
          badgeType="neutral"
        />
        <StatCard
          title="Data Quality Score"
          value={validationReport ? `${validationReport.quality_score}%` : "Uncomputed"}
          subValue={validationReport ? `Status: ${validationReport.status}` : "Evaluating"}
          icon={ShieldCheck}
          badge={validationReport?.status === "EXCELLENT" ? "Grade A" : "Audited"}
          badgeType={validationReport?.quality_score >= 80 ? "success" : "neutral"}
        />
        <StatCard
          title="Dataset Isolation"
          value="Enforced"
          subValue="No cross-room conflation"
          icon={Database}
          badge="Strict"
          badgeType="success"
        />
      </div>

      {/* Dataset Selector & Query Filter Bar */}
      <div className="glass-panel p-4 rounded-xl border border-border flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 flex-1">
          {/* Dataset Partition Selector */}
          <div>
            <select
              value={selectedDatasetId}
              onChange={(e) => {
                setSelectedDatasetId(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-foreground font-semibold focus:outline-none focus:border-primary"
            >
              {datasets.map((ds) => (
                <option key={ds.dataset_id} value={ds.dataset_id}>
                  {ds.dataset_name} ({ds.total_records} rounds)
                </option>
              ))}
            </select>
          </div>

          {/* Search Box */}
          <div className="relative min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              placeholder="Search Round ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-card border border-border rounded-lg text-xs text-foreground placeholder:text-muted focus:outline-none focus:border-primary"
            />
          </div>

          {/* Sort Order */}
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as any)}
            className="bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary"
          >
            <option value="desc">Timestamp (Newest First)</option>
            <option value="asc">Timestamp (Oldest First)</option>
          </select>

          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={fetchRoundsAndReport}
            className="p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main Canonical Table */}
      <div className="glass-panel rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-muted/60 text-muted uppercase text-[10px] tracking-wider border-b border-border">
              <tr>
                <th className="py-3 px-4">Round ID</th>
                <th className="py-3 px-4">Platform</th>
                <th className="py-3 px-4">Provider</th>
                <th className="py-3 px-4">Room</th>
                <th className="py-3 px-4">Crash Multiplier</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Verification</th>
                <th className="py-3 px-4">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-foreground">
              {roundsData.rounds.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12">
                    <EmptyState
                      title="No Ingested Records in Partition"
                      description="Import genuine historical crash rounds using the CSV or JSON data import pipeline."
                      actionLabel="Import Multiplier File"
                      onAction={() => setShowImportModal(true)}
                      icon="database"
                    />
                  </td>
                </tr>
              ) : (
                roundsData.rounds.map((r: any) => (
                  <tr key={r.round_id} className="hover:bg-surface-muted/30 transition font-mono">
                    <td className="py-3 px-4 font-semibold text-primary">{r.round_id}</td>
                    <td className="py-3 px-4 font-sans">{r.platform_id}</td>
                    <td className="py-3 px-4 font-sans">{r.provider_id}</td>
                    <td className="py-3 px-4 font-sans">{r.room_id}</td>
                    <td className="py-3 px-4 font-bold text-foreground">
                      {Number(r.multiplier).toFixed(2)}x
                    </td>
                    <td className="py-3 px-4 text-muted text-[11px]">{r.round_timestamp}</td>
                    <td className="py-3 px-4 font-sans">
                      <StatusBadge status={r.verification_status} />
                    </td>
                    <td className="py-3 px-4 text-muted font-sans text-[11px]">{r.source_type}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Navigation */}
        <div className="p-4 border-t border-border/60 bg-surface/30 flex items-center justify-between text-xs text-muted">
          <span>
            Page <strong className="text-foreground">{roundsData.page}</strong> of{" "}
            <strong className="text-foreground">{roundsData.total_pages}</strong> (
            {roundsData.total_records} total rounds)
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={!roundsData.has_previous}
              className="p-1.5 rounded bg-surface-muted text-muted hover:text-foreground border border-border/60 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => p + 1)}
              disabled={!roundsData.has_next}
              className="p-1.5 rounded bg-surface-muted text-muted hover:text-foreground border border-border/60 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full p-6 rounded-2xl border border-border shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-border/80">
              <div className="flex items-center space-x-2">
                <FileSpreadsheet className="w-5 h-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">Import Historical Multiplier Records</h3>
              </div>
              <button
                onClick={() => setShowImportModal(false)}
                className="p-1 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFileUpload} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-foreground font-semibold mb-1">Target Dataset</label>
                <p className="text-[11px] text-primary font-mono">{selectedDatasetId}</p>
              </div>

              <div>
                <label className="block text-foreground font-semibold mb-1">File Format</label>
                <div className="flex gap-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      checked={importType === "csv"}
                      onChange={() => setImportType("csv")}
                    />
                    <span>CSV (.csv)</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      checked={importType === "json"}
                      onChange={() => setImportType("json")}
                    />
                    <span>JSON / NDJSON (.json)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-foreground font-semibold mb-1">Select File</label>
                <input
                  type="file"
                  accept={importType === "csv" ? ".csv" : ".json"}
                  onChange={(e) => setImportFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-muted file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:bg-surface-muted file:text-foreground file:font-semibold"
                />
              </div>

              {importStatus && (
                <div className="p-3 rounded-lg bg-surface-muted/60 border border-border text-[11px] text-foreground">
                  {importStatus}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-border/80">
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="px-4 py-2 rounded-lg bg-surface-muted hover:bg-surface-border text-foreground transition font-semibold"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!importFile || importing}
                  className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white transition font-semibold disabled:opacity-50"
                >
                  {importing ? "Processing..." : "Start Batch Import"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
