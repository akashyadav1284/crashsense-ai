"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import { config } from "@/config";
import {
  Radio,
  Activity,
  Layers,
  Clock,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Sliders,
  CheckCircle2,
  XCircle,
  Wifi,
  WifiOff,
} from "lucide-react";

export default function LiveMonitorPage() {
  const [selectedPlatform, setSelectedPlatform] = useState("1xbet");
  const [selectedProvider, setSelectedProvider] = useState("spribe");
  const [selectedRoom, setSelectedRoom] = useState("standard");
  const [liveRounds, setLiveRounds] = useState<any[]>([]);
  const [connectors, setConnectors] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any | null>(null);
  const [socketConnected, setSocketConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [reconnecting, setReconnecting] = useState<boolean>(false);

  const fetchTelemetry = async () => {
    try {
      setLoading(true);
      const [roundsData, connData, metData] = await Promise.all([
        api.getLiveRounds({ platformId: selectedPlatform, providerId: selectedProvider, limit: 30 }).catch(() => []),
        api.getRealtimeConnections().catch(() => []),
        api.getRealtimeOperationalMetrics().catch(() => null),
      ]);
      setLiveRounds(roundsData);
      setConnectors(connData);
      setMetrics(metData);
    } catch (err) {
      console.error("Telemetry fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();

    // Establish WebSocket connection for real-time live events
    let ws: WebSocket | null = null;
    try {
      const wsUrl = config.wsUrl || "ws://localhost:8000/ws/telemetry";
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setSocketConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event && payload.event.startsWith("round_")) {
            const updatedRound = payload.data;
            setLiveRounds((prev) => {
              const idx = prev.findIndex((r) => r.round_id === updatedRound.round_id);
              if (idx >= 0) {
                const next = [...prev];
                next[idx] = updatedRound;
                return next;
              }
              return [updatedRound, ...prev.slice(0, 29)];
            });
          }
        } catch {
          // ignore parsing error
        }
      };

      ws.onclose = () => {
        setSocketConnected(false);
      };

      ws.onerror = () => {
        setSocketConnected(false);
      };
    } catch {
      setSocketConnected(false);
    }

    const interval = setInterval(fetchTelemetry, 6000);
    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, [selectedPlatform, selectedProvider]);

  const handleManualReconnect = async () => {
    setReconnecting(true);
    try {
      const targetConnId = `conn-${selectedPlatform}-${selectedProvider === "spribe" ? "aviator" : "crash"}`;
      await api.reconnectConnector(targetConnId).catch(() => {});
      await fetchTelemetry();
    } finally {
      setReconnecting(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Live Multiplier Telemetry Feed"
          description="Real-time WebSocket event ingestion, live round state machine, and low-latency multiplier monitoring."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Monitoring", href: "/live-monitor" },
            { label: "Live Telemetry" },
          ]}
          action={
            <div className="flex items-center gap-3">
              <span
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                  socketConnected
                    ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/30"
                    : "bg-rose-950/40 text-rose-400 border-rose-500/30"
                }`}
              >
                {socketConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
                {socketConnected ? "WebSocket Connected" : "WebSocket Disconnected"}
              </span>

              <button
                onClick={handleManualReconnect}
                disabled={reconnecting}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#263247] bg-[#111827] text-xs text-slate-300 hover:bg-[#0D1220] transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reconnecting ? "animate-spin text-purple-400" : ""}`} />
                Reconnect Feed
              </button>
            </div>
          }
        />

        {/* SCIENTIFIC CAUTION BANNER */}
        <div className="p-4 rounded-xl border border-blue-500/30 bg-blue-950/20 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
          <div className="text-xs space-y-1 text-slate-300">
            <span className="font-semibold text-blue-300">Ground Truth Integrity Mandate:</span>
            <p className="text-slate-400">
              Final multipliers are recorded strictly after an authorized platform event broadcast. Crash multipliers are independent pseudo-random variables; future outcomes cannot be pre-determined.
            </p>
          </div>
        </div>

        {/* SELECTORS & OPERATIONAL METRICS */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827] space-y-3">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Partition Selector
            </span>
            <div className="space-y-2 text-xs">
              <div>
                <label className="text-slate-500 text-[10px] block mb-0.5">Platform</label>
                <select
                  value={selectedPlatform}
                  onChange={(e) => setSelectedPlatform(e.target.value)}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-2.5 py-1.5 text-slate-200 outline-none"
                >
                  <option value="1xbet">1xBet</option>
                  <option value="bcgame">BC.Game</option>
                  <option value="spribe">Spribe Global</option>
                  <option value="historical_replay">Historical Replay (Sandbox)</option>
                </select>
              </div>
              <div>
                <label className="text-slate-500 text-[10px] block mb-0.5">Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full bg-[#0D1220] border border-[#263247] rounded-lg px-2.5 py-1.5 text-slate-200 outline-none"
                >
                  <option value="spribe">Spribe</option>
                  <option value="bc_originals">BC Originals</option>
                  <option value="sandbox">Sandbox Feed</option>
                </select>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Events Processed</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {metrics?.events_processed ?? 0}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-2">
              <span>Rejected: {metrics?.events_rejected ?? 0}</span>
              <span>Duplicates: {metrics?.duplicate_events ?? 0}</span>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Processing Latency</span>
            <div className="text-2xl font-bold text-emerald-400 mt-2">
              {metrics?.average_processing_latency_ms?.toFixed(1) ?? "0.0"} <span className="text-xs text-slate-400">ms</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">End-to-end ingestion pipeline</div>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <span className="text-[11px] text-slate-400">Active Connectors</span>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {connectors.filter((c) => c.status === "HEALTHY").length} / {connectors.length}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Authorized real-time streams</div>
          </div>
        </div>

        {/* LIVE ROUND FEED TABLE */}
        <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-100 font-semibold text-sm">
              <Radio className="w-4 h-4 text-purple-400 animate-pulse" />
              <span>Live Round Stream ({selectedPlatform} / {selectedProvider})</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {liveRounds.length} Rounds Monitored
            </span>
          </div>

          {loading && liveRounds.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" /> Loading live rounds...
            </div>
          ) : liveRounds.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No live rounds captured on this partition yet. Awaiting authorized event stream or replay event.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-[#0D1220] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#263247]">
                  <tr>
                    <th className="py-2.5 px-3">Round ID</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Multiplier</th>
                    <th className="py-2.5 px-3">Received Time</th>
                    <th className="py-2.5 px-3">Freshness</th>
                    <th className="py-2.5 px-3">Verification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#263247]/60">
                  {liveRounds.map((r) => (
                    <tr key={r.round_id} className="hover:bg-[#0D1220]/50 transition">
                      <td className="py-2.5 px-3 font-mono text-purple-300 font-semibold">{r.round_id}</td>
                      <td className="py-2.5 px-3">
                        <StatusBadge
                          status={
                            r.status === "COMPLETED"
                              ? "PASS"
                              : r.status === "STARTED" || r.status === "ACTIVE"
                              ? "ACTIVE"
                              : "STANDBY"
                          }
                        />
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-100">
                        {r.actual_multiplier != null ? (
                          <span
                            className={
                              r.actual_multiplier >= 2.0 ? "text-emerald-400" : "text-slate-300"
                            }
                          >
                            {r.actual_multiplier.toFixed(2)}x
                          </span>
                        ) : (
                          <span className="text-slate-500 italic">In flight...</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                        {new Date(r.event_received_timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">
                        {r.data_freshness_ms} ms
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            r.verification_status === "VERIFIED"
                              ? "bg-emerald-950/40 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {r.verification_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
