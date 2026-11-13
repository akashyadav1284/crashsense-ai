"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/services/apiClient";
import {
  ShieldCheck,
  Users,
  Activity,
  FileText,
  Key,
  Database,
  Lock,
  RefreshCw,
  UserCheck,
  UserX,
  AlertOctagon,
} from "lucide-react";

export default function AdminPage() {
  const [dashboard, setDashboard] = useState<any | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [accessDenied, setAccessDenied] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string>("");

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const [dash, uList, logs] = await Promise.all([
        api.getAdminDashboard(),
        api.getAdminUsers(),
        api.getAdminAuditLogs(),
      ]);
      setDashboard(dash);
      setUsers(uList);
      setAuditLogs(logs);
      setAccessDenied(false);
    } catch (err: any) {
      console.error("Admin dashboard fetch error:", err);
      if (err.message && err.message.includes("403")) {
        setAccessDenied(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleToggleUserStatus = async (user: any) => {
    const newStatus = user.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE";
    const reason = prompt(`Enter reason for switching ${user.display_name} to ${newStatus}:`, "Administrative review");
    if (!reason) return;

    try {
      await api.updateAdminUserStatus(user.user_id, newStatus, reason);
      setActionMsg(`User ${user.display_name} status updated to ${newStatus}.`);
      await loadAdminData();
    } catch (err: any) {
      setActionMsg(`Failed to update user: ${err.message}`);
    }
  };

  if (accessDenied) {
    return (
      <AppShell>
        <div className="py-24 text-center">
          <Lock className="w-12 h-12 text-rose-400 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-100">Access Restricted</h2>
          <p className="text-xs text-slate-400 mt-1">Administrator (ADMIN / SUPER_ADMIN) role required to access the console.</p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <PageHeader
          title="Administrative Security & Control Console"
          description="Role-based access control (RBAC), user account lifecycle management, and immutable security audit logs."
          breadcrumbs={[
            { label: "Dashboard", href: "/" },
            { label: "Administration" },
            { label: "Admin Panel" },
          ]}
          action={
            <button
              onClick={loadAdminData}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#263247] bg-[#111827] text-xs font-semibold text-slate-300 hover:bg-[#0D1220] transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Console
            </button>
          }
        />

        {actionMsg && (
          <div className="p-3 rounded-lg bg-[#111827] border border-[#263247] text-xs text-purple-300 font-mono">
            {actionMsg}
          </div>
        )}

        {/* ADMIN KPI OVERVIEW */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Total Users</span>
              <Users className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{dashboard?.total_users ?? 0}</p>
            <p className="text-[11px] text-slate-500 mt-1">
              Active: {dashboard?.active_users ?? 0} | Suspended: {dashboard?.suspended_users ?? 0}
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>System Security State</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-emerald-400 mt-2">ENFORCED</p>
            <p className="text-[11px] text-slate-500 mt-1">RBAC server-side authorization</p>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Audit Log Trail</span>
              <FileText className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">{auditLogs.length} Events</p>
            <p className="text-[11px] text-slate-500 mt-1">Immutable security ledger</p>
          </div>

          <div className="p-4 rounded-xl border border-[#263247] bg-[#111827]">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>Connector Governance</span>
              <Activity className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-2">HEALTHY</p>
            <p className="text-[11px] text-slate-500 mt-1">Replay sandbox active</p>
          </div>
        </div>

        {/* USER MANAGEMENT TABLE */}
        <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              <span>User Directory & Status Control</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">{users.length} Registered</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0D1220] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#263247]">
                <tr>
                  <th className="py-2.5 px-3">User</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Created</th>
                  <th className="py-2.5 px-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#263247]/50">
                {users.map((u) => (
                  <tr key={u.user_id} className="hover:bg-[#0D1220]/40">
                    <td className="py-2.5 px-3">
                      <div className="font-semibold text-slate-100">{u.display_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{u.email}</div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-purple-950/40 text-purple-300 border border-purple-500/30">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge
                        status={u.status === "ACTIVE" ? "HEALTHY" : u.status === "SUSPENDED" ? "DEGRADED" : "REJECTED"}
                      />
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-2.5 px-3">
                      {u.role !== "SUPER_ADMIN" ? (
                        <button
                          onClick={() => handleToggleUserStatus(u)}
                          className={`px-2.5 py-1 rounded text-xs font-semibold transition ${
                            u.status === "ACTIVE"
                              ? "bg-rose-950/30 text-rose-300 border border-rose-500/30 hover:bg-rose-900/40"
                              : "bg-emerald-950/30 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-900/40"
                          }`}
                        >
                          {u.status === "ACTIVE" ? "Suspend" : "Reactivate"}
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-500 italic">Protected</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* SECURITY AUDIT LOG TRAIL */}
        <div className="rounded-xl border border-[#263247] bg-[#111827] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" />
              <span>Immutable Security Audit Log</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Recent 10 Entries</span>
          </div>

          <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-[#0D1220] text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-[#263247]">
                <tr>
                  <th className="py-2 px-3">Timestamp</th>
                  <th className="py-2 px-3">Actor</th>
                  <th className="py-2 px-3">Action</th>
                  <th className="py-2 px-3">Target</th>
                  <th className="py-2 px-3">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#263247]/50">
                {auditLogs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-[#0D1220]/40 font-mono text-[11px]">
                    <td className="py-2 px-3 text-slate-400">{new Date(log.timestamp).toLocaleTimeString()}</td>
                    <td className="py-2 px-3 text-purple-300">{log.actor_user_id} ({log.actor_role})</td>
                    <td className="py-2 px-3 font-semibold text-slate-200">{log.action}</td>
                    <td className="py-2 px-3 text-slate-400">{log.target_resource}</td>
                    <td className="py-2 px-3">
                      <span className="text-emerald-400">{log.outcome}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
