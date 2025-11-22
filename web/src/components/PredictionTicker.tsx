"use client";

import { useEffect, useState } from "react";
import type { Prediction, PredictionsPayload } from "@/types/prediction";
import { selectCurrentSlate } from "@/lib/data";
import { getPredictionGrade } from "@/lib/prediction";

const numberFmt = (value: number) => `${(value * 100).toFixed(1)}%`;

function getTopEdges(preds: Prediction[], count = 3) {
  return preds.slice().sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge)).slice(0, count);
}

export function PredictionTicker({ initial }: { initial: PredictionsPayload }) {
  const [payload, setPayload] = useState<PredictionsPayload>(initial);

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        const res = await fetch("/api/predictions", { cache: "no-store" });
        if (!res.ok) return;
        const data = (await res.json()) as PredictionsPayload;
        if (!cancelled) {
          setPayload(data);
        }
      } catch (err) {
        console.error("Prediction ticker refresh failed", err);
      }
    }

    refresh();
    const interval = setInterval(refresh, 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const currentSlate = selectCurrentSlate(payload.games);
  const topEdges = getTopEdges(currentSlate);

  return (
    <div className="card-elevated p-5 text-sm text-white/85 md:p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-2 w-2 rounded-full bg-sky-400 animate-pulse-subtle" />
          <p className="text-xs uppercase tracking-[0.32em] text-white/60">Live prediction ticker</p>
        </div>
        <p className="text-[0.7rem] uppercase tracking-[0.26em] text-white/50">Auto-refresh every 60s</p>
      </div>

      <ul className="mt-5 space-y-3">
        {topEdges.map((game) => (
          <li
            key={game.id}
            className="ticker-row hover:border-white/20 hover:shadow-lg"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 text-white">
              <span className="font-semibold tracking-wide">
                {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
              </span>
              <span className="badge text-[11px] uppercase tracking-[0.28em] text-cyan-200">
                {getPredictionGrade(game.edge).label} grade
              </span>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-white/70">
              <span className="inline-flex items-center gap-2">
                <span className="text-white/50">Edge</span>
                <span className="font-semibold text-sky-200">
                  {numberFmt(game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb)}
                </span>
                <span className="text-white/50">→</span>
                <span>{game.modelFavorite === "home" ? game.homeTeam.abbrev : game.awayTeam.abbrev}</span>
              </span>
              <span className="text-white/50">{game.startTimeEt ?? "TBD"}</span>
            </div>
            <SparkBar value={Math.abs(game.edge)} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function SparkBar({ value }: { value: number }) {
  const pct = Math.min(Math.abs(value) * 100, 25); // cap at 25 pts
  return (
    <div className="h-1.5 w-full rounded-full bg-white/10">
      <div
        className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-sky-400 to-blue-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
