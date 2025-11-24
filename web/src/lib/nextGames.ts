import { getCurrentStandings } from "@/lib/current";

export type NextGameInfo = { opponent: string; date: string; startTimeEt: string | null };

const nameToAbbrev = new Map<string, string>(getCurrentStandings().map((team) => [team.team, team.abbrev]));

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
  const cand = team?.abbreviation || team?.triCode || nameToAbbrev.get(team?.name) || team?.teamName || team?.name;
  return (cand || "").toString().toUpperCase();
};

export async function fetchNextGamesMap(abbrevs: string[], lookaheadDays = 14): Promise<Record<string, NextGameInfo>> {
  const today = new Date();
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  const start = fmt(today);
  const end = fmt(new Date(today.getTime() + lookaheadDays * 24 * 60 * 60 * 1000));
  const url = `https://statsapi.web.nhl.com/api/v1/schedule?startDate=${start}&endDate=${end}`;

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return {};
    const data = await res.json();
    const map: Record<string, NextGameInfo> = {};

    data?.dates?.forEach((block: any) => {
      const date = block?.date;
      block?.games?.forEach((game: any) => {
        const homeTeam = game?.teams?.home?.team;
        const awayTeam = game?.teams?.away?.team;
        const home = resolveAbbrev(homeTeam);
        const away = resolveAbbrev(awayTeam);
        const startTimeEt = formatEt(game?.gameDate);
        if (home && !map[home]) map[home] = { opponent: away, date, startTimeEt };
        if (away && !map[away]) map[away] = { opponent: home, date, startTimeEt };
      });
    });

    const filtered: Record<string, NextGameInfo> = {};
    abbrevs.forEach((abbr) => {
      if (map[abbr]) filtered[abbr] = map[abbr];
    });
    return filtered;
  } catch {
    return {};
  }
}
