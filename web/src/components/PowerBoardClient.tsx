"use client";

import React from "react";
import { TeamCrest } from "@/components/TeamCrest";

type NextGameInfo = { opponent: string; date: string; startTimeEt: string | null };

export type LeaderboardRow = {
  powerRank: number;
  standingsRank: number;
  movement: number;
  team: string;
  abbrev: string;
  record: string;
  points: number;
  goalDifferential: number;
  pointPctg: number;
  powerScore: number;
  overlay?: { avgProb: number };
};

function formatPct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

const nameFallback: Record<string, string> = {};

export function PowerBoardClient({ rows }: { rows: LeaderboardRow[] }) {
  const [nextGames, setNextGames] = React.useState<Record<string, NextGameInfo>>({});

  React.useEffect(() => {
    const fetchNextGames = async () => {
      const today = new Date();
      const end = new Date();
      end.setDate(end.getDate() + 14);
      const fmt = (d: Date) => d.toISOString().slice(0, 10);
      const url = `https://statsapi.web.nhl.com/api/v1/schedule?startDate=${fmt(today)}&endDate=${fmt(end)}`;
      try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const map: Record<string, NextGameInfo> = {};
        const formatEt = (iso: string) => {
          if (!iso) return null;
          const dt = new Date(iso);
          return new Intl.DateTimeFormat("en-US", {
            timeZone: "America/New_York",
            hour: "numeric",
            minute: "2-digit",
          }).format(dt);
        };
        data?.dates?.forEach((block: any) => {
          const date = block?.date;
          block?.games?.forEach((game: any) => {
            const home = game?.teams?.home?.team?.abbreviation || game?.teams?.home?.team?.triCode;
            const away = game?.teams?.away?.team?.abbreviation || game?.teams?.away?.team?.triCode;
            const startTimeEt = formatEt(game?.gameDate);
            if (home && !map[home]) map[home] = { opponent: away, date, startTimeEt };
            if (away && !map[away]) map[away] = { opponent: home, date, startTimeEt };
          });
        });
        setNextGames(map);
      } catch (err) {
        console.warn("schedule fetch failed", err);
      }
    };
    fetchNextGames();
  }, []);

  const renderRow = (row: LeaderboardRow) => {
    const movementDisplay = row.movement === 0 ? "Even" : row.movement > 0 ? `+${row.movement}` : row.movement;
    const movementTone = row.movement > 0 ? "movement--positive" : row.movement < 0 ? "movement--negative" : "movement--neutral";
    const overlayProb = row.overlay ? formatPct(row.overlay.avgProb) : "—";
    const next = nextGames[row.abbrev];
    const nextDisplay = next
      ? `${next.opponent} (${next.date}${next.startTimeEt ? ` · ${next.startTimeEt} ET` : ""})`
      : "Next game TBA";

    return (
      <div className="power-board__row" key={row.abbrev}>
        <div className="rank-chip">#{row.powerRank}</div>
        <div className="power-team">
          <TeamCrest abbrev={row.abbrev} />
          <div>
            <p className="power-name">{row.team}</p>
            <p className="micro-label">Standings #{row.standingsRank}</p>
          </div>
        </div>
        <span className={`movement movement--pillless ${movementTone}`}>{movementDisplay}</span>
        <span className="power-data">{row.record}</span>
        <span className="power-data">{formatPct(row.pointPctg)}</span>
        <span className={`power-data ${row.goalDifferential >= 0 ? "text-up" : "text-down"}`}>
          {row.goalDifferential >= 0 ? "+" : ""}
          {row.goalDifferential}
        </span>
        <span className="power-data">{overlayProb}</span>
        <span className="power-data">{nextDisplay}</span>
      </div>
    );
  };

  return (
    <div className="power-board">
      <div className="power-board__head">
        <span>#</span>
        <span>Team</span>
        <span>Movement</span>
        <span>Record</span>
        <span>Point %</span>
        <span>Goal Diff</span>
        <span>Model Win%</span>
        <span>Next</span>
      </div>
      {rows.map(renderRow)}
    </div>
  );
}
