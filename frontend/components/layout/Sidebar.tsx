"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useNavigationStore } from "@/hooks/useStore";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Radio,
  Network,
  History,
  BarChart3,
  FlaskConical,
  BrainCircuit,
  TrendingUp,
  Cpu,
  Coins,
  SlidersHorizontal,
  ShieldAlert,
  Bell,
  HeartPulse,
  Settings,
  ShieldCheck,
  Camera,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

const NAVIGATION: NavGroup[] = [
  {
    group: "OVERVIEW",
    items: [
      { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    group: "MONITORING",
    items: [
      { name: "Live Monitor", href: "/live-monitor", icon: Radio },
      { name: "Platform Connections", href: "/platforms", icon: Network },
      { name: "Historical Rounds", href: "/historical-rounds", icon: History },
    ],
  },
  {
    group: "ANALYTICS",
    items: [
      { name: "Multiplier Analytics", href: "/analytics", icon: BarChart3 },
      { name: "Screenshot Analysis", href: "/screenshot-analysis", icon: Camera },
      { name: "Statistical Laboratory", href: "/statistical-lab", icon: FlaskConical },
      { name: "ML Research Lab", href: "/ml-lab", icon: BrainCircuit },
      { name: "Model Performance", href: "/ml-lab/performance", icon: TrendingUp },
      { name: "Prediction History", href: "/predictions", icon: Cpu },
    ],
  },
  {
    group: "SIMULATION",
    items: [
      { name: "Paper Trading", href: "/paper-trading", icon: Coins },
      { name: "Strategy Laboratory", href: "/paper-trading/strategies", icon: SlidersHorizontal },
      { name: "Risk Management", href: "/risk-management", icon: ShieldAlert },
    ],
  },
  {
    group: "SYSTEM",
    items: [
      { name: "Notifications", href: "/notifications", icon: Bell },
      { name: "System Health", href: "/system-health", icon: HeartPulse },
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
  {
    group: "ADMINISTRATION",
    items: [
      { name: "Admin Panel", href: "/admin", icon: ShieldCheck },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useNavigationStore();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 flex flex-col bg-sidebar border-r border-border transition-all duration-300 ease-in-out select-none",
        sidebarOpen ? "w-64" : "w-20"
      )}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border/80">
        <Link href="/dashboard" className="flex items-center space-x-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center font-black text-white text-base shadow-lg shadow-primary/25 shrink-0">
            <Zap className="w-5 h-5 fill-white text-white" />
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <span className="font-extrabold tracking-wider text-sm bg-gradient-to-r from-foreground via-slate-200 to-muted bg-clip-text text-transparent truncate">
                CRASHSENSE <span className="text-brand-neon font-black">AI</span>
              </span>
              <span className="text-[10px] text-muted font-medium tracking-widest uppercase">
                Enterprise v1.0
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          className="p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition"
        >
          {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAVIGATION.map((group) => (
          <div key={group.group}>
            {sidebarOpen ? (
              <p className="px-3 text-[10px] font-bold text-muted/70 tracking-widest uppercase mb-2">
                {group.group}
              </p>
            ) : (
              <div className="h-px bg-border/60 my-2 mx-2" />
            )}
            <div className="space-y-1">
              {group.items.map((item) => {
                const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={!sidebarOpen ? item.name : undefined}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 group",
                      active
                        ? "bg-primary/15 text-primary border border-primary/30"
                        : "text-muted hover:text-foreground hover:bg-surface-muted/60 border border-transparent"
                    )}
                  >
                    <Icon
                      className={cn(
                        "w-4 h-4 shrink-0 transition-colors",
                        active ? "text-primary" : "text-muted group-hover:text-foreground"
                      )}
                    />
                    {sidebarOpen && <span className="truncate">{item.name}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer / Telemetry Status */}
      <div className="p-3 border-t border-border/80 bg-surface/30">
        <div
          className={cn(
            "flex items-center gap-2.5 p-2 rounded-lg bg-surface-muted/60 border border-border/60 text-xs",
            !sidebarOpen && "justify-center"
          )}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          {sidebarOpen && (
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-foreground text-[11px] truncate">
                Telemetry Pipeline
              </span>
              <span className="text-[10px] text-muted truncate">Zero-Leakage Active</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

