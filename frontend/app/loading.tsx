export default function Loading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-slate-300">
      <div className="relative flex items-center justify-center">
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-surface-border border-t-brand-purple border-r-brand-cyan"></div>
        <div className="absolute text-xs font-semibold text-brand-neon tracking-widest uppercase">CS</div>
      </div>
      <p className="mt-4 text-sm font-medium tracking-wide text-slate-400">Loading CrashSense AI...</p>
    </div>
  );
}

