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
    <div className="rounded-3xl border border-white/10 bg-black/20 p-4 text-sm text-white/80">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.5em] text-white/60">Live edges</p>
        <p className="text-[0.65rem] uppercase tracking-[0.5em] text-white/40">Auto-refresh</p>
      </div>
      <ul className="mt-3 space-y-2">
        {topEdges.map((game) => (
          <li key={game.id} className="space-y-1">
            <div className="flex items-center justify-between text-white">
              <span className="font-semibold">
                {game.awayTeam.abbrev} @ {game.homeTeam.abbrev}
              </span>
              <span className="text-xs uppercase tracking-[0.4em] text-cyan-200">
                {getPredictionGrade(game.edge).label}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-white/70">
              <span>
                {game.modelFavorite === "home" ? game.homeTeam.abbrev : game.awayTeam.abbrev} → {numberFmt(
                  game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb,
                )}
              </span>
              <span>{game.startTimeEt ?? "TBD"}</span>
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
