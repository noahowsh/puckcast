"use client";

import Link from "next/link";
import { useMemo } from "react";
import { getPredictionsPayload } from "@/lib/data";
import { getCurrentStandings, computeStandingsPowerScore } from "@/lib/current";
import type { CurrentStanding } from "@/lib/current";
import type { Prediction } from "@/types/prediction";
import { getPredictionGrade } from "@/lib/prediction";
import { TeamCrest } from "@/components/TeamCrest";
import { teamGradient } from "@/lib/teamColors";

const payload = getPredictionsPayload();
const standings = getCurrentStandings();
const standingsByAbbrev = new Map(standings.map((t) => [t.abbrev, t]));

function getGameById(gameId: string): Prediction | undefined {
  return payload.games.find((g) => g.id === gameId);
}

function getTeamStanding(abbrev: string): (CurrentStanding & { rank: number }) | undefined {
  return standingsByAbbrev.get(abbrev);
}

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatRecord(standing: CurrentStanding & { rank: number }): string {
  return `${standing.wins}-${standing.losses}-${standing.ot}`;
}

type ComparisonStat = {
  label: string;
  home: string | number;
  away: string | number;
  homeRaw: number;
  awayRaw: number;
  higherIsBetter: boolean;
};

function StatBar({ stat }: { stat: ComparisonStat }) {
  const total = stat.homeRaw + stat.awayRaw;
  const homePct = total > 0 ? (stat.homeRaw / total) * 100 : 50;
  const homeWins = stat.higherIsBetter ? stat.homeRaw > stat.awayRaw : stat.homeRaw < stat.awayRaw;
  const awayWins = stat.higherIsBetter ? stat.awayRaw > stat.homeRaw : stat.awayRaw < stat.homeRaw;

  return (
    <div className="stat-comparison">
      <div className="stat-comparison__row">
        <span className={`stat-comparison__value ${homeWins ? "stat-comparison__value--leader" : ""}`}>
          {stat.home}
        </span>
        <span className="stat-comparison__label">{stat.label}</span>
        <span className={`stat-comparison__value ${awayWins ? "stat-comparison__value--leader" : ""}`}>
          {stat.away}
        </span>
      </div>
      <div className="stat-comparison__bar">
        <div
          className="stat-comparison__fill stat-comparison__fill--home"
          style={{ width: `${homePct}%` }}
        />
        <div
          className="stat-comparison__fill stat-comparison__fill--away"
          style={{ width: `${100 - homePct}%` }}
        />
      </div>
    </div>
  );
}

function WinProbCircle({ prob, team, isModelPick }: { prob: number; team: string; isModelPick: boolean }) {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - prob * circumference;

  return (
    <div className="prob-circle">
      <svg viewBox="0 0 100 100" className="prob-circle__svg">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={isModelPick ? "var(--mint)" : "rgba(255,255,255,0.3)"}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      <div className="prob-circle__content">
        <span className="prob-circle__pct">{pct(prob)}</span>
        <span className="prob-circle__team">{team}</span>
      </div>
    </div>
  );
}

export default function MatchupPage({ params }: { params: { gameId: string } }) {
  const game = getGameById(params.gameId);

  if (!game) {
    return (
      <div className="min-h-screen">
        <div className="container">
          <section className="nova-hero">
            <div className="nova-hero__text">
              <h1 className="display-xl">Matchup not found</h1>
              <p className="lead">This game may have already been played or doesn&apos;t exist.</p>
              <Link href="/predictions" className="cta cta-primary">
                Back to predictions
              </Link>
            </div>
          </section>
        </div>
      </div>
    );
  }

  const homeStanding = getTeamStanding(game.homeTeam.abbrev);
  const awayStanding = getTeamStanding(game.awayTeam.abbrev);
  const grade = getPredictionGrade(game.edge);
  const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
  const favoriteProb = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;
  const edgePts = Math.abs(game.edge * 100);

  const homePowerScore = homeStanding ? computeStandingsPowerScore(homeStanding) : 0;
  const awayPowerScore = awayStanding ? computeStandingsPowerScore(awayStanding) : 0;

  const comparisonStats: ComparisonStat[] = useMemo(() => {
    if (!homeStanding || !awayStanding) return [];

    return [
      {
        label: "Points",
        home: homeStanding.points,
        away: awayStanding.points,
        homeRaw: homeStanding.points,
        awayRaw: awayStanding.points,
        higherIsBetter: true,
      },
      {
        label: "Point %",
        home: pct(homeStanding.pointPctg),
        away: pct(awayStanding.pointPctg),
        homeRaw: homeStanding.pointPctg,
        awayRaw: awayStanding.pointPctg,
        higherIsBetter: true,
      },
      {
        label: "Goal Diff",
        home: homeStanding.goalDifferential >= 0 ? `+${homeStanding.goalDifferential}` : homeStanding.goalDifferential,
        away: awayStanding.goalDifferential >= 0 ? `+${awayStanding.goalDifferential}` : awayStanding.goalDifferential,
        homeRaw: homeStanding.goalDifferential + 100,
        awayRaw: awayStanding.goalDifferential + 100,
        higherIsBetter: true,
      },
      {
        label: "Goals/Game",
        home: (homeStanding.goalsForPerGame ?? 0).toFixed(2),
        away: (awayStanding.goalsForPerGame ?? 0).toFixed(2),
        homeRaw: homeStanding.goalsForPerGame ?? 0,
        awayRaw: awayStanding.goalsForPerGame ?? 0,
        higherIsBetter: true,
      },
      {
        label: "Goals Against/Game",
        home: (homeStanding.goalsAgainstPerGame ?? 0).toFixed(2),
        away: (awayStanding.goalsAgainstPerGame ?? 0).toFixed(2),
        homeRaw: homeStanding.goalsAgainstPerGame ?? 0,
        awayRaw: awayStanding.goalsAgainstPerGame ?? 0,
        higherIsBetter: false,
      },
      {
        label: "Power Score",
        home: homePowerScore,
        away: awayPowerScore,
        homeRaw: homePowerScore,
        awayRaw: awayPowerScore,
        higherIsBetter: true,
      },
    ];
  }, [homeStanding, awayStanding, homePowerScore, awayPowerScore]);

  const formatGameDate = (dateStr: string) => {
    const date = new Date(dateStr + "T12:00:00");
    return new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric" }).format(date);
  };

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Hero header with both teams */}
        <section className="matchup-hero">
          <div className="matchup-hero__bg">
            <div className="matchup-hero__gradient matchup-hero__gradient--away" style={{ background: teamGradient(game.awayTeam.abbrev) }} />
            <div className="matchup-hero__gradient matchup-hero__gradient--home" style={{ background: teamGradient(game.homeTeam.abbrev) }} />
          </div>

          <div className="matchup-hero__content">
            <div className="matchup-hero__meta">
              <Link href="/predictions" className="breadcrumb">
                ← Back to predictions
              </Link>
              <div className="pill-row">
                <span className="pill">{formatGameDate(game.gameDate)}</span>
                <span className="pill">{game.startTimeEt ?? "TBD"}</span>
                {game.venue && <span className="pill">{game.venue}</span>}
              </div>
            </div>

            <div className="matchup-hero__versus">
              <div className="matchup-hero__team matchup-hero__team--away">
                <TeamCrest abbrev={game.awayTeam.abbrev} size={80} />
                <div className="matchup-hero__team-info">
                  <h2 className="matchup-hero__team-name">{game.awayTeam.name}</h2>
                  {awayStanding && (
                    <p className="matchup-hero__record">{formatRecord(awayStanding)} · #{awayStanding.rank} in standings</p>
                  )}
                </div>
              </div>

              <div className="matchup-hero__at">
                <span>@</span>
              </div>

              <div className="matchup-hero__team matchup-hero__team--home">
                <TeamCrest abbrev={game.homeTeam.abbrev} size={80} />
                <div className="matchup-hero__team-info">
                  <h2 className="matchup-hero__team-name">{game.homeTeam.name}</h2>
                  {homeStanding && (
                    <p className="matchup-hero__record">{formatRecord(homeStanding)} · #{homeStanding.rank} in standings</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Model prediction section */}
        <section className="nova-section">
          <div className="matchup-grid">
            {/* Win probabilities */}
            <div className="bento-card matchup-probs">
              <p className="micro-label">Win probabilities</p>
              <div className="matchup-probs__circles">
                <WinProbCircle
                  prob={game.awayWinProb}
                  team={game.awayTeam.abbrev}
                  isModelPick={game.modelFavorite === "away"}
                />
                <WinProbCircle
                  prob={game.homeWinProb}
                  team={game.homeTeam.abbrev}
                  isModelPick={game.modelFavorite === "home"}
                />
              </div>
            </div>

            {/* Model pick card */}
            <div className="bento-card matchup-pick">
              <p className="micro-label">Model pick</p>
              <div className="matchup-pick__content">
                <TeamCrest abbrev={favorite.abbrev} size={50} />
                <div>
                  <h3 className="matchup-pick__team">{favorite.name}</h3>
                  <p className="matchup-pick__prob">{pct(favoriteProb)} win probability</p>
                </div>
              </div>
              <div className="matchup-pick__details">
                <div className="matchup-pick__stat">
                  <span className="matchup-pick__stat-value">{grade.label}</span>
                  <span className="matchup-pick__stat-label">Grade</span>
                </div>
                <div className="matchup-pick__stat">
                  <span className="matchup-pick__stat-value">{edgePts.toFixed(1)}</span>
                  <span className="matchup-pick__stat-label">Edge pts</span>
                </div>
                <div className="matchup-pick__stat">
                  <span className="matchup-pick__stat-value">{game.confidenceScore.toFixed(2)}</span>
                  <span className="matchup-pick__stat-label">Confidence</span>
                </div>
              </div>
              <p className="matchup-pick__summary">{game.summary}</p>
            </div>

            {/* Projected goalies */}
            {game.projectedGoalies && (game.projectedGoalies.home || game.projectedGoalies.away) && (
              <div className="bento-card matchup-goalies">
                <p className="micro-label">Projected goalies</p>
                <div className="matchup-goalies__grid">
                  {game.projectedGoalies.away && (
                    <div className="matchup-goalies__entry">
                      <span className="matchup-goalies__team">{game.awayTeam.abbrev}</span>
                      <span className="matchup-goalies__name">{game.projectedGoalies.away.name}</span>
                      <span className="chip-soft">{game.projectedGoalies.away.record}</span>
                      <span className="chip-soft">{game.projectedGoalies.away.restDays}d rest</span>
                    </div>
                  )}
                  {game.projectedGoalies.home && (
                    <div className="matchup-goalies__entry">
                      <span className="matchup-goalies__team">{game.homeTeam.abbrev}</span>
                      <span className="matchup-goalies__name">{game.projectedGoalies.home.name}</span>
                      <span className="chip-soft">{game.projectedGoalies.home.record}</span>
                      <span className="chip-soft">{game.projectedGoalies.home.restDays}d rest</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Team comparison stats */}
        {comparisonStats.length > 0 && (
          <section className="nova-section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Side by side</p>
                <h2>Team comparison</h2>
                <p className="lead-sm">Season stats for both teams heading into this matchup.</p>
              </div>
            </div>

            <div className="bento-card matchup-stats">
              <div className="matchup-stats__header">
                <div className="matchup-stats__team">
                  <TeamCrest abbrev={game.awayTeam.abbrev} />
                  <span>{game.awayTeam.abbrev}</span>
                </div>
                <span className="matchup-stats__vs">vs</span>
                <div className="matchup-stats__team">
                  <TeamCrest abbrev={game.homeTeam.abbrev} />
                  <span>{game.homeTeam.abbrev}</span>
                </div>
              </div>
              <div className="matchup-stats__list">
                {comparisonStats.map((stat) => (
                  <StatBar key={stat.label} stat={stat} />
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Special teams comparison */}
        {game.specialTeams && (game.specialTeams.home || game.specialTeams.away) && (
          <section className="nova-section">
            <div className="section-head">
              <div>
                <p className="eyebrow">Special teams</p>
                <h2>Power play & penalty kill</h2>
              </div>
            </div>

            <div className="matchup-special-teams">
              {game.specialTeams.away && (
                <div className="bento-card">
                  <div className="matchup-special__header">
                    <TeamCrest abbrev={game.awayTeam.abbrev} />
                    <span>{game.awayTeam.name}</span>
                  </div>
                  <div className="matchup-special__stats">
                    {game.specialTeams.away.powerPlayPct != null && (
                      <div className="matchup-special__stat">
                        <span className="matchup-special__value">{pct(game.specialTeams.away.powerPlayPct)}</span>
                        <span className="matchup-special__label">Power Play %</span>
                      </div>
                    )}
                    {game.specialTeams.away.opponentPenaltyKillPct != null && (
                      <div className="matchup-special__stat">
                        <span className="matchup-special__value">{pct(game.specialTeams.away.opponentPenaltyKillPct)}</span>
                        <span className="matchup-special__label">Opp PK %</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              {game.specialTeams.home && (
                <div className="bento-card">
                  <div className="matchup-special__header">
                    <TeamCrest abbrev={game.homeTeam.abbrev} />
                    <span>{game.homeTeam.name}</span>
                  </div>
                  <div className="matchup-special__stats">
                    {game.specialTeams.home.powerPlayPct != null && (
                      <div className="matchup-special__stat">
                        <span className="matchup-special__value">{pct(game.specialTeams.home.powerPlayPct)}</span>
                        <span className="matchup-special__label">Power Play %</span>
                      </div>
                    )}
                    {game.specialTeams.home.opponentPenaltyKillPct != null && (
                      <div className="matchup-special__stat">
                        <span className="matchup-special__value">{pct(game.specialTeams.home.opponentPenaltyKillPct)}</span>
                        <span className="matchup-special__label">Opp PK %</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Team page links */}
        <section className="nova-section">
          <div className="matchup-links">
            <Link href={`/teams/${game.awayTeam.abbrev}`} className="cta cta-ghost">
              View {game.awayTeam.name} page
            </Link>
            <Link href={`/teams/${game.homeTeam.abbrev}`} className="cta cta-ghost">
              View {game.homeTeam.name} page
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
