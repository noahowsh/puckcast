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

  const map: Record<string, NextGameInfo> = {};

  for (let offset = 0; offset < lookaheadDays; offset += 1) {
    const target = new Date(today);
    target.setDate(today.getDate() + offset);
    const url = `https://api-web.nhle.com/v1/schedule/${fmt(target)}?expand=schedule.teams`;
    try {
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
      // Early exit if we've filled all abbrevs
      if (abbrevs.every((a) => map[a])) break;
    } catch {
      continue;
    }
  }

  const filtered: Record<string, NextGameInfo> = {};
  abbrevs.forEach((abbr) => {
    if (map[abbr]) filtered[abbr] = map[abbr];
  });
  return filtered;
}
