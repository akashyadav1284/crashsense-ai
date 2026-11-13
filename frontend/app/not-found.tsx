import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-6 text-center">
      <div className="glass-panel max-w-md w-full p-8 rounded-2xl border border-surface-border glass-glow-cyan">
        <span className="text-6xl font-black bg-gradient-to-r from-brand-purple via-brand-neon to-brand-cyan bg-clip-text text-transparent">
          404
        </span>
        <h2 className="text-xl font-bold text-white mt-4 mb-2">Resource Route Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">
          The requested subsystem route does not exist or has been migrated.
        </p>
        <Link
          href="/"
          className="inline-flex items-center justify-center px-5 py-2.5 bg-gradient-to-r from-brand-purple to-brand-blue hover:opacity-90 text-white rounded-lg text-sm font-semibold transition"
        >
          Return to Mission Control
        </Link>
      </div>
    </div>
  );
}

