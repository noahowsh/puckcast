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
    <div className="card-elevated p-5 text-xs text-white/75 md:p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="uppercase tracking-[0.32em] text-white/60">Start odds monitor</p>
        <p className="text-[0.65rem] uppercase tracking-[0.26em] text-white/50">Auto-refresh every 2m</p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {payload.goalies.slice(0, 3).map((goalie) => (
          <div key={goalie.name} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3 shadow-inner shadow-black/20">
            <p className="text-[0.6rem] uppercase tracking-[0.3em] text-white/50">{goalie.team}</p>
            <p className="text-base font-semibold text-white">{goalie.name}</p>
            <p className="text-sm text-cyan-200">{Math.round(goalie.startLikelihood * 100)}% start</p>
            <div className="mt-2 h-1.5 w-full rounded-full bg-white/10">
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
