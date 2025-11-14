import predictionsPayload from "@/data/todaysPredictions.json";
import goaliePulse from "@/data/goaliePulse.json";
import standingsSnapshot from "@/data/currentStandings.json";
import type { StatusSnapshot } from "@/types/status";

const toDate = (value: unknown): Date | null => {
  if (typeof value !== "string" || !value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const minutesSince = (value: unknown): number | null => {
  const date = toDate(value);
  if (!date) return null;
  return Math.max(Math.round((Date.now() - date.getTime()) / 60000), 0);
};

export function buildStatusSnapshot(): StatusSnapshot {
  const games = Array.isArray((predictionsPayload as any).games) ? (predictionsPayload as any).games.length : 0;
  const goalieGames = goaliePulse?.tonight?.games ?? [];
  const projectedStarters = goalieGames.reduce((total: number, game: any) => total + (game?.home ? 1 : 0) + (game?.away ? 1 : 0), 0);

  return {
    generatedAt: new Date().toISOString(),
    predictions: {
      generatedAt: (predictionsPayload as any).generatedAt ?? null,
      games,
      staleMinutes: minutesSince((predictionsPayload as any).generatedAt),
    },
    goalies: {
      updatedAt: goaliePulse?.updatedAt ?? null,
      projectedGames: goalieGames.length,
      projectedStarters,
      staleMinutes: minutesSince(goaliePulse?.updatedAt),
    },
    standings: {
      generatedAt: (standingsSnapshot as any).generatedAt ?? null,
      teams: Array.isArray((standingsSnapshot as any).teams) ? (standingsSnapshot as any).teams.length : 0,
      staleMinutes: minutesSince((standingsSnapshot as any).generatedAt),
    },
    deploy: {
      commit: process.env.VERCEL_GIT_COMMIT_SHA ?? null,
      branch: process.env.VERCEL_GIT_COMMIT_REF ?? null,
      env: process.env.VERCEL_ENV ?? process.env.NODE_ENV ?? null,
    },
  };
}
