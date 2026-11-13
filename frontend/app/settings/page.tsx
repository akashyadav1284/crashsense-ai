"use client";

import React, { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/services/apiClient";
import {
  User,
  Sliders,
  Bell,
  Shield,
  Palette,
  Database,
  Save,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";

export default function SettingsPage() {
  const [profile, setProfile] = useState<any | null>(null);
  const [displayName, setDisplayName] = useState<string>("Lead Quantitative Researcher");
  const [email, setEmail] = useState<string>("researcher@crashsense.ai");
  const [notificationsEnabled, setNotificationsEnabled] = useState<boolean>(true);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>("");

  const loadProfile = async () => {
    try {
      const [u, pref] = await Promise.all([
        api.getMyProfile().catch(() => null),
        api.getMyPreferences().catch(() => null),
      ]);
      if (u) {
        setProfile(u);
        setDisplayName(u.display_name);
        setEmail(u.email);
      }
      if (pref) {
        setNotificationsEnabled(pref.notifications_enabled);
        setSoundEnabled(pref.sound_enabled);
      }
    } catch (err) {
      console.error("Settings load error:", err);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg("");
    try {
      await Promise.all([
        api.updateMyProfile({ display_name: displayName }),
        api.updateMyPreferences({
          notifications_enabled: notificationsEnabled,
          sound_enabled: soundEnabled,
        }),
      ]);
      setStatusMsg("Profile settings and notification preferences successfully updated.");
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to update settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Application Settings & Preferences"
        description="Configure analytical defaults, notification dispatch triggers, visual tokens, and account authentication settings."
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "System" },
          { label: "Settings" },
        ]}
      />

      {statusMsg && (
        <div className="p-3 rounded-lg bg-[#111827] border border-[#263247] text-xs text-purple-300 font-mono">
          {statusMsg}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <div className="p-6 rounded-xl border border-[#263247] bg-[#111827] space-y-4">
          <div className="flex items-center space-x-3 pb-4 border-b border-[#263247]">
            <User className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="text-sm font-bold text-slate-100">User Profile</h3>
              <p className="text-xs text-slate-400">Account identity and role authorization</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Display Name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-3 py-2 bg-[#0D1220] border border-[#263247] rounded-lg text-slate-200 outline-none"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-3 py-2 bg-[#0D1220] border border-[#263247] rounded-lg text-slate-500 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Assigned Role</label>
              <span className="inline-block px-2.5 py-1 rounded text-xs font-mono font-semibold bg-purple-950/40 text-purple-300 border border-purple-500/30">
                {profile?.role ?? "USER"}
              </span>
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Account Status</label>
              <span className="inline-block px-2.5 py-1 rounded text-xs font-mono font-semibold bg-emerald-950/40 text-emerald-300 border border-emerald-500/30">
                {profile?.status ?? "ACTIVE"}
              </span>
            </div>
          </div>
        </div>

        {/* Notification Preferences Card */}
        <div className="p-6 rounded-xl border border-[#263247] bg-[#111827] space-y-4">
          <div className="flex items-center space-x-3 pb-4 border-b border-[#263247]">
            <Bell className="w-5 h-5 text-purple-400" />
            <div>
              <h3 className="text-sm font-bold text-slate-100">Notification Preferences</h3>
              <p className="text-xs text-slate-400">Configure dispatch channels and audio alert triggers</p>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notificationsEnabled}
                onChange={(e) => setNotificationsEnabled(e.target.checked)}
                className="rounded border-[#263247] bg-[#0D1220] text-purple-600 focus:ring-0"
              />
              <span className="text-slate-300">Enable in-app real-time notification broadcasts</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={soundEnabled}
                onChange={(e) => setSoundEnabled(e.target.checked)}
                className="rounded border-[#263247] bg-[#0D1220] text-purple-600 focus:ring-0"
              />
              <span className="text-slate-300">Play audio cue on critical alert dispatches</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white transition disabled:opacity-50"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Settings
          </button>
        </div>
      </form>
    </AppShell>
  );
}
