"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application runtime error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-6 text-center">
      <div className="glass-panel max-w-md w-full p-8 rounded-2xl border border-surface-border glass-glow-purple">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-red-500/10 text-red-400 mb-4 border border-red-500/20">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">System Encountered An Error</h2>
        <p className="text-sm text-slate-400 mb-6">
          The requested interface component failed to render. Please attempt to reset the session.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-brand-purple hover:bg-brand-purple/90 text-white rounded-lg text-sm font-medium transition"
          >
            Retry Execution
          </button>
          <Link
            href="/"
            className="px-4 py-2 bg-surface-muted hover:bg-surface-border text-slate-300 rounded-lg text-sm font-medium transition"
          >
            Return Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

