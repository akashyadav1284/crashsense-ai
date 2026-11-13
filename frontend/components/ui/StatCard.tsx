import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: LucideIcon;
  badge?: string;
  badgeType?: "success" | "warning" | "danger" | "neutral";
  className?: string;
}

export function StatCard({
  title,
  value,
  subValue,
  icon: Icon,
  badge,
  badgeType = "neutral",
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        "glass-panel p-5 rounded-xl border border-border relative overflow-hidden transition-all duration-200 hover:border-border/90",
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-muted uppercase tracking-wider">
          {title}
        </span>
        <div className="w-8 h-8 rounded-lg bg-surface-muted flex items-center justify-center text-muted border border-border/80">
          <Icon className="w-4 h-4 text-primary" />
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-2xl font-black text-foreground tracking-tight">
            {value}
          </div>
          {subValue && (
            <p className="text-[11px] text-muted mt-1 flex items-center gap-1 font-medium">
              {subValue}
            </p>
          )}
        </div>

        {badge && (
          <span
            className={cn(
              "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
              badgeType === "success" &&
                "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
              badgeType === "warning" &&
                "bg-amber-500/10 text-amber-400 border-amber-500/20",
              badgeType === "danger" &&
                "bg-rose-500/10 text-rose-400 border-rose-500/20",
              badgeType === "neutral" &&
                "bg-slate-500/10 text-slate-400 border-slate-500/20"
            )}
          >
            {badge}
          </span>
        )}
      </div>
    </div>
  );
}

