import React from "react";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status:
    | "CONNECTED"
    | "DISCONNECTED"
    | "AUTHORIZATION REQUIRED"
    | "ERROR"
    | "NOT CONFIGURED"
    | "VERIFIED"
    | "UNVERIFIED"
    | "DISPUTED"
    | "ACTIVE"
    | "TRAINING"
    | "EVALUATED"
    | "STANDBY"
    | "ARCHIVED"
    | "PASS"
    | "FAIL"
    | "PENDING"
    | "HEALTHY"
    | "DEGRADED"
    | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const norm = (status || "").toUpperCase();

  let variantStyles = "bg-slate-500/10 text-slate-400 border-slate-500/20";
  let dotColor = "bg-slate-400";

  if (["CONNECTED", "VERIFIED", "ACTIVE", "PASS", "HEALTHY", "WON"].includes(norm)) {
    variantStyles = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    dotColor = "bg-emerald-400";
  } else if (["DISCONNECTED", "NOT CONFIGURED", "STANDBY"].includes(norm)) {
    variantStyles = "bg-blue-500/10 text-blue-400 border-blue-500/30";
    dotColor = "bg-blue-400";
  } else if (["AUTHORIZATION REQUIRED", "PENDING", "DEGRADED", "TRAINING"].includes(norm)) {
    variantStyles = "bg-amber-500/10 text-amber-400 border-amber-500/30";
    dotColor = "bg-amber-400 animate-pulse";
  } else if (["ERROR", "FAIL", "DISPUTED", "LOST"].includes(norm)) {
    variantStyles = "bg-rose-500/10 text-rose-400 border-rose-500/30";
    dotColor = "bg-rose-400";
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border tracking-wider uppercase",
        variantStyles,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", dotColor)} />
      {status}
    </span>
  );
}

