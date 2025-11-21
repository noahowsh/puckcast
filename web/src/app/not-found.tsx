import Link from "next/link";

export default function NotFound() {
  return (
    <div className="relative flex min-h-[80vh] items-center justify-center overflow-hidden px-6">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(14,165,233,0.1),transparent_50%)]" />
      </div>

      <div className="relative z-10 mx-auto max-w-2xl text-center">
        {/* Error code */}
        <div className="mb-8">
          <h1 className="text-[150px] font-bold leading-none bg-gradient-to-r from-sky-400 via-cyan-400 to-sky-500 bg-clip-text text-transparent sm:text-[200px]">
            404
          </h1>
          <div className="mt-4 h-1 w-32 mx-auto rounded-full bg-gradient-to-r from-sky-400 to-cyan-400" />
        </div>

        {/* Message */}
        <div className="space-y-4">
          <h2 className="text-3xl font-semibold text-white sm:text-4xl">
            Looks like you hit the crossbar.
          </h2>
          <p className="text-lg text-white/70 max-w-md mx-auto">
            The page you're looking for doesn't exist. Maybe it got traded to another site, or perhaps it never existed at all.
          </p>
        </div>

        {/* Actions */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/"
            className="rounded-full bg-gradient-to-r from-sky-500 to-cyan-500 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white shadow-lg shadow-sky-500/30 transition-all hover:shadow-xl hover:shadow-sky-500/40 hover:scale-105"
          >
            Back to Home
          </Link>
          <Link
            href="/predictions"
            className="rounded-full border border-white/20 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white/80 transition-all hover:text-white hover:border-white/40"
          >
            View Predictions
          </Link>
        </div>

        {/* Fun hockey reference */}
        <div className="mt-12 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <p className="text-sm text-white/60">
            <span className="text-sky-400">🏒 Pro tip:</span> Use the navigation above to find what you're looking for, or head back to the home page to see today's predictions.
          </p>
        </div>
      </div>
    </div>
  );
}
