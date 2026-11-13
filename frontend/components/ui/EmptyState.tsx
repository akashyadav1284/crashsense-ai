import React from "react";
import { AlertCircle, Database, Server, RefreshCw } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: "database" | "server" | "alert";
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon = "database",
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center rounded-xl border border-border bg-card/60 backdrop-blur-sm">
      <div className="w-14 h-14 rounded-2xl bg-surface-muted flex items-center justify-center text-muted mb-4 border border-border">
        {icon === "database" && <Database className="w-6 h-6 text-primary" />}
        {icon === "server" && <Server className="w-6 h-6 text-secondary" />}
        {icon === "alert" && <AlertCircle className="w-6 h-6 text-warning" />}
      </div>
      <h3 className="text-base font-bold text-foreground mb-1">{title}</h3>
      <p className="text-xs text-muted max-w-sm mb-6 leading-relaxed">
        {description}
      </p>
      {actionLabel && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-muted hover:bg-surface-border text-xs font-semibold text-foreground border border-border transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionLabel}
        </button>
      )}
    </div>
  );
}

