"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useNavigationStore } from "@/hooks/useStore";
import { api } from "@/services/apiClient";
import { HealthState, NotificationItem } from "@/types";
import {
  Menu,
  Search,
  Bell,
  HeartPulse,
  User,
  Shield,
  ExternalLink,
  ChevronDown,
} from "lucide-react";

export function Navbar() {
  const { toggleSidebar } = useNavigationStore();
  const [health, setHealth] = useState<HealthState | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    api
      .getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));

    api
      .getNotifications()
      .then(setNotifications)
      .catch(() => setNotifications([]));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <header className="sticky top-0 z-20 h-16 bg-sidebar/85 backdrop-blur-md border-b border-border px-4 lg:px-8 flex items-center justify-between">
      {/* Left controls */}
      <div className="flex items-center space-x-4">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle navigation drawer"
          className="p-2 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Global Search */}
        <div className="relative hidden md:block w-72 lg:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            placeholder="Search rounds, platforms, models (e.g. #9812, 1xBet)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-card border border-border rounded-lg text-xs text-foreground placeholder:text-muted focus:outline-none focus:border-primary transition"
          />
        </div>
      </div>

      {/* Right Subsystem Actions */}
      <div className="flex items-center space-x-3">
        {/* System Health Quick Pill */}
        <Link
          href="/system-health"
          className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-border bg-card hover:bg-surface-muted transition text-xs"
        >
          <HeartPulse
            className={`w-4 h-4 ${
              health?.status === "healthy" ? "text-emerald-400" : "text-amber-400 animate-pulse"
            }`}
          />
          <span className="text-muted font-medium">Gateway:</span>
          <span
            className={`font-bold ${
              health?.status === "healthy" ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {health?.status ? health.status.toUpperCase() : "CHECKING"}
          </span>
        </Link>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            aria-label="Toggle notifications center"
            className="p-2 rounded-lg text-muted hover:text-foreground hover:bg-surface-muted transition relative"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary animate-ping" />
            )}
          </button>

          {showNotifs && (
            <div className="absolute right-0 mt-2 w-80 glass-panel rounded-xl border border-border shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between pb-2 border-b border-border/80">
                <span className="text-xs font-bold text-foreground">Notifications</span>
                <span className="text-[10px] text-muted">{unreadCount} unread</span>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-border/40 py-1">
                {notifications.length === 0 ? (
                  <p className="text-xs text-muted text-center py-4">No recent notifications</p>
                ) : (
                  notifications.map((n) => (
                    <div key={n.id} className="py-2 px-1 hover:bg-surface-muted/40 rounded transition">
                      <p className="text-xs font-semibold text-foreground">{n.title}</p>
                      <p className="text-[11px] text-muted mt-0.5 line-clamp-2">{n.message}</p>
                    </div>
                  ))
                )}
              </div>
              <Link
                href="/notifications"
                onClick={() => setShowNotifs(false)}
                className="block text-center pt-2 text-[11px] font-semibold text-primary hover:underline"
              >
                View all notifications
              </Link>
            </div>
          )}
        </div>

        {/* User Menu / Avatar */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            aria-label="Toggle account profile menu"
            className="flex items-center space-x-2 p-1.5 rounded-lg hover:bg-surface-muted transition"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-secondary flex items-center justify-center font-bold text-white text-xs shadow-md shadow-primary/20">
              AD
            </div>
            <div className="hidden lg:flex flex-col text-left">
              <span className="text-xs font-bold text-foreground">Chief Quant</span>
              <span className="text-[10px] text-muted font-medium">Administrator</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-muted hidden lg:block" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-52 glass-panel rounded-xl border border-border shadow-2xl p-2 z-50">
              <div className="px-3 py-2 border-b border-border/80">
                <p className="text-xs font-bold text-foreground">Akash S.</p>
                <p className="text-[10px] text-muted truncate">chief.quant@crashsense.ai</p>
              </div>
              <div className="py-1">
                <Link
                  href="/settings"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-muted hover:text-foreground hover:bg-surface-muted transition"
                >
                  <User className="w-3.5 h-3.5 text-muted" />
                  Account Settings
                </Link>
                <Link
                  href="/admin"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-muted hover:text-foreground hover:bg-surface-muted transition"
                >
                  <Shield className="w-3.5 h-3.5 text-muted" />
                  Admin Console
                </Link>
              </div>
              <div className="border-t border-border/80 pt-1">
                <Link
                  href="/docs"
                  target="_blank"
                  className="flex items-center justify-between px-3 py-2 rounded-lg text-[11px] text-primary hover:bg-surface-muted transition"
                >
                  <span>System Documentation</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

