"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to console (could integrate with error tracking service)
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="relative flex min-h-[80vh] items-center justify-center overflow-hidden px-6">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(239,68,68,0.1),transparent_50%)]" />
      </div>

      <div className="relative z-10 mx-auto max-w-2xl text-center">
        {/* Error icon */}
        <div className="mb-8">
          <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full border-4 border-red-500/20 bg-red-500/10">
            <svg
              className="h-12 w-12 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        {/* Message */}
        <div className="space-y-4">
          <h2 className="text-3xl font-semibold text-white sm:text-4xl">
            Something went wrong
          </h2>
          <p className="text-lg text-white/70 max-w-md mx-auto">
            We hit an unexpected error. Don&apos;t worry, our model is still working hard on predictions. Try refreshing the page or heading back home.
          </p>
        </div>

        {/* Error details (only shown in development) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mt-6 rounded-2xl border border-red-500/20 bg-red-500/5 p-4 text-left">
            <p className="text-xs font-mono text-red-400">
              {error.message}
            </p>
            {error.digest && (
              <p className="mt-2 text-xs text-white/40">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={reset}
            className="rounded-full bg-gradient-to-r from-red-500 to-orange-500 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white shadow-lg shadow-red-500/30 transition-all hover:shadow-xl hover:shadow-red-500/40 hover:scale-105"
          >
            Try Again
          </button>
          <Link
            href="/"
            className="rounded-full border border-white/20 px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-white/80 transition-all hover:text-white hover:border-white/40"
          >
            Back to Home
          </Link>
        </div>

        {/* Support info */}
        <div className="mt-12 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <p className="text-sm text-white/60">
            If this error persists, please let us know on{" "}
            <a
              href="https://x.com/puckcastai"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-400 hover:text-sky-300 underline"
            >
              @puckcastai
            </a>
            {" "}so we can fix it.
          </p>
        </div>
      </div>
    </div>
  );
}
