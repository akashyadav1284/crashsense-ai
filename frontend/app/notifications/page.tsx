"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/services/apiClient";
import {
  Bell,
  CheckCheck,
  AlertTriangle,
  Info,
  ShieldAlert,
  CheckCircle,
  Trash2,
  RefreshCw,
  Filter,
} from "lucide-react";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(true);
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const params = filterType !== "ALL" ? { type: filterType } : undefined;
      const [items, countRes] = await Promise.all([
        api.getNotifications(params).catch(() => []),
        api.getUnreadNotificationCount().catch(() => ({ unread_count: 0 })),
      ]);
      setNotifications(items);
      setUnreadCount(countRes.unread_count);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [filterType]);

  const markAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      await loadNotifications();
    } catch (err) {
      console.error("Failed to mark all read:", err);
    }
  };

  const markSingleRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      await loadNotifications();
    } catch (err) {
      console.error("Failed to mark read:", err);
    }
  };

  const deleteSingle = async (id: string) => {
    try {
      await api.deleteNotification(id);
      await loadNotifications();
    } catch (err) {
      console.error("Failed to delete notification:", err);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Notification Center & Operational Alerts"
        description="Audit log of system telemetry dispatches, ML laboratory validation results, and risk circuit-breaker notices."
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "System", href: "/system-health" },
          { label: "Notifications" },
        ]}
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={loadNotifications}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#263247] bg-[#111827] text-xs font-semibold text-slate-300 hover:bg-[#0D1220] transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <button
              onClick={markAllRead}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition"
            >
              <CheckCheck className="w-3.5 h-3.5" /> Mark All as Read
            </button>
          </div>
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-[#263247] pb-3 text-xs">
        <div className="flex items-center gap-2">
          {["ALL", "SYSTEM", "SECURITY", "RISK", "ML_RESEARCH", "CONNECTOR"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1 rounded-lg transition font-medium ${
                filterType === t
                  ? "bg-purple-600 text-white"
                  : "bg-[#111827] text-slate-400 hover:text-slate-200 border border-[#263247]"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <span className="text-slate-400 font-mono text-[11px]">{unreadCount} Unread</span>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {loading && notifications.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-purple-400" /> Loading notifications...
          </div>
        ) : notifications.length === 0 ? (
          <div className="py-16 text-center text-slate-500 text-xs border border-[#263247] rounded-xl bg-[#111827]">
            <Bell className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            No notifications in this category. All systems normal.
          </div>
        ) : (
          notifications.map((n) => {
            const isRead = n.is_read;
            const sev = n.severity;
            return (
              <div
                key={n.notification_id}
                className={`p-4 rounded-xl border transition flex items-start justify-between gap-4 ${
                  isRead
                    ? "bg-[#111827]/60 border-[#263247]"
                    : "bg-[#111827] border-purple-500/50 shadow-sm"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {sev === "CRITICAL" || sev === "ERROR" ? (
                      <ShieldAlert className="w-5 h-5 text-rose-400" />
                    ) : sev === "WARNING" ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    ) : (
                      <Info className="w-5 h-5 text-purple-400" />
                    )}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-100">{n.title}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-400">
                        {n.notification_type}
                      </span>
                      {!isRead && (
                        <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" />
                      )}
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{n.message}</p>
                    <span className="text-[10px] text-slate-500 font-mono block">
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {!isRead && (
                    <button
                      onClick={() => markSingleRead(n.notification_id)}
                      className="text-xs text-purple-400 hover:text-purple-300 font-medium px-2 py-1 rounded bg-[#0D1220] border border-[#263247]"
                    >
                      Mark Read
                    </button>
                  )}
                  <button
                    onClick={() => deleteSingle(n.notification_id)}
                    className="text-slate-500 hover:text-rose-400 p-1"
                    title="Delete notification"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </AppShell>
  );
}
