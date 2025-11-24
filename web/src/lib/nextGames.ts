import { getCurrentStandings } from "@/lib/current";
import predictionsPayloadRaw from "@/data/todaysPredictions.json";

export type NextGameInfo = { opponent: string; date: string; startTimeEt: string | null };

const standings = getCurrentStandings();
const nameToAbbrev = new Map<string, string>(standings.map((team) => [team.team.toLowerCase(), team.abbrev]));
const abbrevSet = new Set(standings.map((t) => t.abbrev));

const formatEt = (iso: string | undefined) => {
  if (!iso) return null;
  const dt = new Date(iso);
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
  }).format(dt);
};

const resolveAbbrev = (team: any) => {
  const rawName = (team?.name || team?.teamName || team?.commonName?.default || team?.placeName?.default || "").toString().toLowerCase();
  const cand =
    team?.abbrev ||
    team?.abbreviation ||
    team?.triCode ||
    nameToAbbrev.get(rawName) ||
    nameToAbbrev.get((team?.teamName || "").toString().toLowerCase()) ||
    nameToAbbrev.get((team?.commonName?.default || "").toString().toLowerCase()) ||
    nameToAbbrev.get((team?.placeName?.default || "").toString().toLowerCase());
  const up = (cand || "").toString().toUpperCase();
  return abbrevSet.has(up) ? up : "";
};

export async function fetchNextGamesMap(abbrevs: string[], lookaheadDays = 14): Promise<Record<string, NextGameInfo>> {
  const today = new Date();
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  const start = fmt(today);
  const end = fmt(new Date(today.getTime() + lookaheadDays * 24 * 60 * 60 * 1000));
  const map: Record<string, NextGameInfo> = {};

  // Seed from current predictions payload (only if gameDate is today or in the future)
  const predictions = predictionsPayloadRaw as { games?: any[] };
  const games = predictions?.games || [];
  games.forEach((game: any) => {
    const home = (game?.homeTeam?.abbrev || "").toString().toUpperCase();
    const away = (game?.awayTeam?.abbrev || "").toString().toUpperCase();
    const date = game?.gameDate;
    const startEt = game?.startTimeEt || formatEt(game?.startTimeUtc);
    if (date && date < start) return; // skip past
    if (home && !map[home]) map[home] = { opponent: away, date, startTimeEt: startEt ?? null };
    if (away && !map[away]) map[away] = { opponent: home, date, startTimeEt: startEt ?? null };
  });

  // Overlay with NHL schedule (per-day loop on api-web.nhle.com) to fill missing teams or better dates
  for (let offset = 0; offset < lookaheadDays; offset += 1) {
    const target = new Date(today.getTime() + offset * 24 * 60 * 60 * 1000);
    const dateStr = fmt(target);
    try {
      const url = `https://api-web.nhle.com/v1/schedule/${dateStr}`;
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) continue;
      const data = await res.json();
      data?.gameWeek?.forEach((block: any) => {
        const date = block?.date;
        block?.games?.forEach((game: any) => {
          const home = resolveAbbrev(game?.homeTeam);
          const away = resolveAbbrev(game?.awayTeam);
          const startTimeEt = formatEt(game?.startTimeUTC);
          if (home && !map[home]) map[home] = { opponent: away, date, startTimeEt };
          if (away && !map[away]) map[away] = { opponent: home, date, startTimeEt };
        });
      });
      // Early exit if all teams filled
      if (abbrevs.every((a) => map[a])) break;
    } catch {
      continue;
    }
  }

  const filtered: Record<string, NextGameInfo> = {};
  abbrevs.forEach((abbr) => {
    if (map[abbr]) filtered[abbr] = map[abbr];
    else filtered[abbr] = { opponent: "TBD", date: null as any, startTimeEt: null };
  });
  return filtered;
}
