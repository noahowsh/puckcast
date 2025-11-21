export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="relative">
        {/* Spinning puck */}
        <div className="h-16 w-16 animate-spin rounded-full border-4 border-slate-700 border-t-sky-400" />

        {/* Glow effect */}
        <div className="absolute inset-0 h-16 w-16 animate-pulse rounded-full bg-sky-500/20 blur-xl" />

        {/* Loading text */}
        <p className="mt-6 text-center text-sm uppercase tracking-[0.4em] text-white/60">
          Loading...
        </p>
      </div>
    </div>
  );
}
