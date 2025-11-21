"use client";

import { useEffect, useState } from "react";
import type { GoaliePulse } from "@/types/goalie";

export function GoalieTicker({ initial }: { initial: GoaliePulse }) {
  const [payload, setPayload] = useState<GoaliePulse>(initial);

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        const res = await fetch("/api/goalies", { cache: "no-store" });
        if (!res.ok) return;
        const data = (await res.json()) as GoaliePulse;
        if (!cancelled) {
          setPayload(data);
        }
      } catch (err) {
        console.error("Goalie ticker refresh failed", err);
      }
    }

    refresh();
    const interval = setInterval(refresh, 120_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-4 text-xs text-white/70">
      <div className="flex items-center justify-between">
        <p className="uppercase tracking-[0.4em] text-white/60">Start odds monitor</p>
        <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/40">Auto-refresh</p>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        {payload.goalies.slice(0, 3).map((goalie) => (
          <div key={goalie.name} className="rounded-2xl border border-white/10 bg-black/30 p-3">
            <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/50">{goalie.team}</p>
            <p className="text-base text-white">{goalie.name}</p>
            <p className="text-sm text-cyan-200">{Math.round(goalie.startLikelihood * 100)}% start</p>
            <div className="mt-1 h-1.5 w-full rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-300 to-indigo-400"
                style={{ width: `${goalie.startLikelihood * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
