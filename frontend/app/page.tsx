"use client";

import React, { useEffect, useState } from "react";
import { config } from "@/config";
import { HealthState } from "@/types";

export default function HomePage() {
  const [health, setHealth] = useState<HealthState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [mountedTime, setMountedTime] = useState<string>("");

  useEffect(() => {
    setMountedTime(new Date().toUTCString());

    const checkSystemHealth = async () => {
      try {
        const res = await fetch(`${config.apiUrl}/health`, { cache: "no-store" });
        if (res.ok) {
          const data: HealthState = await res.json();
          setHealth(data);
        } else {
          setHealth(null);
        }
      } catch (err) {
        console.warn("Backend not yet reached:", err);
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkSystemHealth();
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col justify-between selection:bg-brand-purple">
      {/* Background Gradients */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-brand-purple/20 blur-[130px] rounded-full pointer-events-none" />
        <div className="absolute top-96 -left-20 w-[450px] h-[450px] bg-brand-cyan/15 blur-[120px] rounded-full pointer-events-none" />
      </div>

      {/* Top Header / Navigation */}
      <header className="relative z-10 border-b border-surface-border/80 bg-surface/60 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-purple to-brand-cyan flex items-center justify-center font-black text-white text-lg shadow-lg shadow-brand-purple/30">
              ⚡
            </div>
            <div>
              <span className="font-extrabold tracking-wider text-lg bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                CRASHSENSE <span className="text-brand-neon font-black">AI</span>
              </span>
              <span className="ml-2 px-2 py-0.5 text-[10px] font-bold tracking-widest uppercase rounded-full bg-brand-purple/20 text-brand-neon border border-brand-purple/40">
                Phase 1: Architecture
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs text-slate-400 border border-surface-border bg-surface-muted/50 px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>System Core v1.0.0</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero & Architectural Shell */}
      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-6 py-12 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Main Info */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-blue/10 border border-brand-blue/30 text-xs font-semibold text-brand-neon">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-neon"></span>
              Institutional Real-Time Telemetry & Predictive Platform
            </div>

            <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white leading-tight">
              Predictive Intelligence for <br />
              <span className="bg-gradient-to-r from-brand-purple via-brand-neon to-brand-cyan bg-clip-text text-transparent">
                High-Frequency Crash Dynamics
              </span>
            </h1>

            <p className="text-base text-slate-300 max-w-xl leading-relaxed">
              Production foundation initialized. Architected with high-concurrency FastAPI async microservices,
              Next.js TypeScript App Router, MongoDB Atlas telemetry persistence, and Redis real-time state bus.
            </p>

            {/* Architecture Metrics Grid */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="glass-panel p-4 rounded-xl border border-surface-border">
                <p className="text-xs text-slate-400 font-medium">Target Latency</p>
                <p className="text-xl font-bold text-white mt-1">&lt; 15ms</p>
                <p className="text-[10px] text-emerald-400 mt-0.5">Async Event Loop</p>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-surface-border">
                <p className="text-xs text-slate-400 font-medium">Database Core</p>
                <p className="text-xl font-bold text-white mt-1">MongoDB Atlas</p>
                <p className="text-[10px] text-brand-neon mt-0.5">Motor Async Driver</p>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-surface-border">
                <p className="text-xs text-slate-400 font-medium">State Bus</p>
                <p className="text-xl font-bold text-white mt-1">Redis</p>
                <p className="text-[10px] text-purple-400 mt-0.5">Low-latency Cache</p>
              </div>
            </div>
          </div>

          {/* Subsystem Readiness Panel */}
          <div className="lg:col-span-5">
            <div className="glass-panel p-6 rounded-2xl border border-surface-border/90 glass-glow-purple space-y-5">
              <div className="flex items-center justify-between border-b border-surface-border/60 pb-4">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Subsystem Diagnostics</h3>
                  <p className="text-xs text-slate-400">Phase 1 Infrastructure Verification</p>
                </div>
                <span className="px-2.5 py-1 text-[11px] font-semibold rounded-md bg-surface-muted text-slate-300 border border-surface-border">
                  {loading ? "Checking..." : health ? "Online" : "Awaiting Backend"}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-muted/40 border border-surface-border/40">
                  <div className="flex items-center space-x-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    <div>
                      <p className="text-xs font-semibold text-white">Next.js Frontend Shell</p>
                      <p className="text-[10px] text-slate-400">TypeScript / Tailwind CSS</p>
                    </div>
                  </div>
                  <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-muted/40 border border-surface-border/40">
                  <div className="flex items-center space-x-3">
                    <span className={`w-2.5 h-2.5 rounded-full ${health ? "bg-emerald-400" : "bg-amber-400"}`}></span>
                    <div>
                      <p className="text-xs font-semibold text-white">FastAPI Async API</p>
                      <p className="text-[10px] text-slate-400">Python 3.13 / Pydantic v2</p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded border ${health ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" : "text-amber-400 bg-amber-500/10 border-amber-500/20"}`}>
                    {health ? "Verified" : "Standby"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-muted/40 border border-surface-border/40">
                  <div className="flex items-center space-x-3">
                    <span className={`w-2.5 h-2.5 rounded-full ${health?.services.mongodb.status === "connected" ? "bg-emerald-400" : "bg-blue-400"}`}></span>
                    <div>
                      <p className="text-xs font-semibold text-white">MongoDB Atlas Layer</p>
                      <p className="text-[10px] text-slate-400">Async Lifecycle & Verification</p>
                    </div>
                  </div>
                  <span className="text-xs font-medium text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                    {health?.services.mongodb.status || "Configured"}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-surface-muted/40 border border-surface-border/40">
                  <div className="flex items-center space-x-3">
                    <span className={`w-2.5 h-2.5 rounded-full ${health?.services.redis.status === "connected" ? "bg-emerald-400" : "bg-purple-400"}`}></span>
                    <div>
                      <p className="text-xs font-semibold text-white">Redis Telemetry Bus</p>
                      <p className="text-[10px] text-slate-400">Low-latency State Ingestion</p>
                    </div>
                  </div>
                  <span className="text-xs font-medium text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                    {health?.services.redis.status || "Configured"}
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-surface-border/60 text-[11px] text-slate-400 flex items-center justify-between">
                <span>API Gateway: <code className="text-slate-300 font-mono">{config.apiUrl}/health</code></span>
                <span className="font-mono text-[10px]">{mountedTime || "Initialized"}</span>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-surface-border/80 bg-surface/40 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <div>
            CRASHSENSE AI © 2026. Production Architecture Foundation.
          </div>
          <div className="flex items-center space-x-4">
            <span className="hover:text-slate-200 transition">Phase 1 Complete</span>
            <span>•</span>
            <span className="hover:text-slate-200 transition">Phase 2 Awaiting Approval</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

