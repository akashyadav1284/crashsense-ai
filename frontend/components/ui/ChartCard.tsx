import React from "react";
import { cn } from "@/lib/utils";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function ChartCard({
  title,
  subtitle,
  action,
  children,
  className,
}: ChartCardProps) {
  return (
    <div
      className={cn(
        "glass-panel p-5 rounded-xl border border-border flex flex-col justify-between",
        className
      )}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 border-b border-border/60 pb-3">
        <div>
          <h3 className="text-sm font-bold text-foreground tracking-wide">
            {title}
          </h3>
          {subtitle && (
            <p className="text-[11px] text-muted mt-0.5">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>

      <div className="w-full flex-1 flex flex-col justify-center min-h-[220px]">
        {children}
      </div>
    </div>
  );
}

