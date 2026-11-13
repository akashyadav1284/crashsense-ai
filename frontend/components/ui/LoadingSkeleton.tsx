import React from "react";
import { cn } from "@/lib/utils";

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-surface-muted/60 border border-border/40",
        className
      )}
    />
  );
}

