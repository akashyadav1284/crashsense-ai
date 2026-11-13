"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  Network,
  Plus,
  Key,
  ShieldCheck,
  Radio,
  FileSpreadsheet,
  AlertCircle,
  X,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";

export default function PlatformsPage() {
  const [platforms, setPlatforms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState<any | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; msg: string; ok: boolean } | null>(null);

  const loadPlatforms = () => {
    setLoading(true);
    api
      .getPlatforms()
      .then((data) => setPlatforms(data))
      .catch(() => setPlatforms([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPlatforms();
  }, []);

  const handleTestConnection = async (platId: string) => {
    setTestingId(platId);
    setTestResult(null);
    try {
      const res = await api.testPlatformConnection(platId);
      setTestResult({
        id: platId,
        msg: res.message || (res.connected ? "Connection verified" : "Disconnected"),
        ok: res.connected,
      });
    } catch (err: any) {
      setTestResult({
        id: platId,
        msg: err.message || "Connection check failed",
        ok: false,
      });
    } finally {
      setTestingId(null);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Platform & Data Feed Connectors"
        description="Configure verified data sources, licensed feeds, and raw telemetry imports. Connectors remain strictly disconnected until valid access credentials are authenticated."
        breadcrumbs={[{ label: "Monitoring" }, { label: "Platform Connections" }]}
        action={
          <button
            onClick={loadPlatforms}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Connectors
          </button>
        }
      />

      {/* Integration Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-border">
          <div className="flex items-center justify-between text-xs text-muted mb-1">
            <span>Official APIs</span>
            <Key className="w-4 h-4 text-primary" />
          </div>
          <p className="text-xl font-black text-foreground">1xbet</p>
          <p className="text-[11px] text-muted mt-1">Status: NOT CONFIGURED</p>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-border">
          <div className="flex items-center justify-between text-xs text-muted mb-1">
            <span>Licensed Feeds</span>
            <ShieldCheck className="w-4 h-4 text-secondary" />
          </div>
          <p className="text-xl font-black text-foreground">spribe</p>
          <p className="text-[11px] text-muted mt-1">Status: AUTH REQUIRED</p>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-border">
          <div className="flex items-center justify-between text-xs text-muted mb-1">
            <span>WebSockets</span>
            <Radio className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-xl font-black text-foreground">bcgame</p>
          <p className="text-[11px] text-muted mt-1">Status: NOT CONFIGURED</p>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-border">
          <div className="flex items-center justify-between text-xs text-muted mb-1">
            <span>File Imports</span>
            <FileSpreadsheet className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-xl font-black text-foreground">CSV / JSON</p>
          <p className="text-[11px] text-emerald-400 font-semibold mt-1">Engine: READY</p>
        </div>
      </div>

      {/* Platform Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {platforms.map((p) => (
          <div
            key={p.platform_id}
            className="glass-panel p-5 rounded-xl border border-border flex flex-col justify-between hover:border-border/90 transition"
          >
            <div>
              <div className="flex items-start justify-between gap-3 mb-3">
                <div>
                  <h3 className="text-sm font-bold text-foreground">{p.platform_name}</h3>
                  <p className="text-[11px] text-muted">Provider: {p.provider_name}</p>
                </div>
                <StatusBadge status={p.connection_status} />
              </div>

              <div className="space-y-2 py-3 border-y border-border/50 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted">Integration Type:</span>
                  <span className="font-semibold text-foreground">{p.integration_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Authorization Status:</span>
                  <span className="font-semibold text-muted font-mono text-[11px]">
                    {p.authorization_status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Last Successful Sync:</span>
                  <span className="text-muted font-mono text-[11px]">
                    {p.last_successful_sync || "Never"}
                  </span>
                </div>
              </div>

              {testResult && testResult.id === p.platform_id && (
                <div
                  className={`mt-3 p-2.5 rounded-lg border text-[11px] flex items-start gap-2 ${
                    testResult.ok
                      ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                      : "bg-surface-muted/60 border-border/80 text-muted"
                  }`}
                >
                  {testResult.ok ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-warning" />
                  )}
                  <span>{testResult.msg}</span>
                </div>
              )}
            </div>

            <div className="mt-5 pt-3 border-t border-border/60 flex items-center justify-between">
              <span className="text-[10px] text-muted font-mono uppercase">
                ID: {p.platform_id}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleTestConnection(p.platform_id)}
                  disabled={testingId === p.platform_id}
                  className="px-2.5 py-1.5 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition disabled:opacity-50"
                >
                  {testingId === p.platform_id ? "Testing..." : "Test Link"}
                </button>
                <button
                  onClick={() => setActiveModal(p)}
                  className="px-2.5 py-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 text-xs font-semibold text-primary border border-primary/40 transition"
                >
                  Configure
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Dialog */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
          <div className="glass-panel max-w-lg w-full p-6 rounded-2xl border border-border shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-border/80">
              <div>
                <h3 className="text-base font-bold text-foreground">
                  Connector Settings: {activeModal.platform_name}
                </h3>
                <p className="text-xs text-muted">ID: {activeModal.platform_id}</p>
              </div>
              <button
                onClick={() => setActiveModal(null)}
                className="p-1 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="p-3 rounded-lg bg-surface-muted/40 border border-border/40 text-[11px] text-muted">
                <strong>Integrity Policy:</strong> Connection parameters remain unverified until genuine TLS handshake responses are received from the target host.
              </div>
              <div className="flex justify-end pt-3 border-t border-border/80">
                <button
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-lg bg-surface-muted hover:bg-surface-border text-foreground transition font-semibold"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
