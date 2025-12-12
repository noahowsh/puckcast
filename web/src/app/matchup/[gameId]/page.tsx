"use client";

import Link from "next/link";
import { use, useMemo } from "react";
import { getPredictionsPayload } from "@/lib/data";
import { getCurrentStandings, computeStandingsPowerScore } from "@/lib/current";
import type { CurrentStanding } from "@/lib/current";
import type { Prediction } from "@/types/prediction";
import { getPredictionGrade } from "@/lib/prediction";
import { TeamCrest } from "@/components/TeamCrest";
import { teamPrimaryColor, getContrastingTeamColor } from "@/lib/teamColors";

const payload = getPredictionsPayload();
const standings = getCurrentStandings();
const standingsByAbbrev = new Map(standings.map((t) => [t.abbrev, t]));

function getGameById(gameId: string): Prediction | undefined {
  return payload.games.find((g) => g.id === gameId);
}

type PageProps = {
  params: Promise<{ gameId: string }>;
};

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
  away: string | number;
  home: string | number;
  awayRaw: number;
  homeRaw: number;
  higherIsBetter: boolean;
};

function StatBar({
  stat,
  awayColor,
  homeColor
}: {
  stat: ComparisonStat;
  awayColor: string;
  homeColor: string;
}) {
  const total = Math.abs(stat.awayRaw) + Math.abs(stat.homeRaw);
  const awayPct = total > 0 ? (Math.abs(stat.awayRaw) / total) * 100 : 50;
  const awayWins = stat.higherIsBetter ? stat.awayRaw > stat.homeRaw : stat.awayRaw < stat.homeRaw;
  const homeWins = stat.higherIsBetter ? stat.homeRaw > stat.awayRaw : stat.homeRaw < stat.awayRaw;

  return (
    <div className="stat-row">
      <div className="stat-row__value" style={{ color: awayWins ? awayColor : undefined }}>
        <span className={awayWins ? "stat-row__leader" : ""}>{stat.away}</span>
      </div>
      <div className="stat-row__center">
        <span className="stat-row__label">{stat.label}</span>
        <div className="stat-row__bar">
          <div
            className="stat-row__fill stat-row__fill--away"
            style={{ width: `${awayPct}%`, background: awayColor }}
          />
          <div
            className="stat-row__fill stat-row__fill--home"
            style={{ width: `${100 - awayPct}%`, background: homeColor }}
          />
        </div>
      </div>
      <div className="stat-row__value stat-row__value--right" style={{ color: homeWins ? homeColor : undefined }}>
        <span className={homeWins ? "stat-row__leader" : ""}>{stat.home}</span>
      </div>
    </div>
  );
}

export default function MatchupPage({ params }: PageProps) {
  const { gameId } = use(params);
  const game = getGameById(gameId);

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
  const underdog = game.modelFavorite === "home" ? game.awayTeam : game.homeTeam;
  const favoriteProb = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;
  const edgePts = Math.abs(game.edge * 100);

  const homePowerScore = homeStanding ? computeStandingsPowerScore(homeStanding) : 0;
  const awayPowerScore = awayStanding ? computeStandingsPowerScore(awayStanding) : 0;

  // Get contrasting team colors for the bars
  const teamColors = getContrastingTeamColor(game.awayTeam.abbrev, game.homeTeam.abbrev);
  const awayColor = teamColors.team1;
  const homeColor = teamColors.team2;

  const comparisonStats: ComparisonStat[] = useMemo(() => {
    if (!homeStanding || !awayStanding) return [];

    return [
      {
        label: "Points",
        away: awayStanding.points,
        home: homeStanding.points,
        awayRaw: awayStanding.points,
        homeRaw: homeStanding.points,
        higherIsBetter: true,
      },
      {
        label: "Point %",
        away: pct(awayStanding.pointPctg),
        home: pct(homeStanding.pointPctg),
        awayRaw: awayStanding.pointPctg,
        homeRaw: homeStanding.pointPctg,
        higherIsBetter: true,
      },
      {
        label: "Goal Diff",
        away: awayStanding.goalDifferential >= 0 ? `+${awayStanding.goalDifferential}` : awayStanding.goalDifferential,
        home: homeStanding.goalDifferential >= 0 ? `+${homeStanding.goalDifferential}` : homeStanding.goalDifferential,
        awayRaw: awayStanding.goalDifferential + 100,
        homeRaw: homeStanding.goalDifferential + 100,
        higherIsBetter: true,
      },
      {
        label: "Goals/Game",
        away: (awayStanding.goalsForPerGame ?? 0).toFixed(2),
        home: (homeStanding.goalsForPerGame ?? 0).toFixed(2),
        awayRaw: awayStanding.goalsForPerGame ?? 0,
        homeRaw: homeStanding.goalsForPerGame ?? 0,
        higherIsBetter: true,
      },
      {
        label: "Goals Against",
        away: (awayStanding.goalsAgainstPerGame ?? 0).toFixed(2),
        home: (homeStanding.goalsAgainstPerGame ?? 0).toFixed(2),
        awayRaw: awayStanding.goalsAgainstPerGame ?? 0,
        homeRaw: homeStanding.goalsAgainstPerGame ?? 0,
        higherIsBetter: false,
      },
      {
        label: "Power Score",
        away: awayPowerScore,
        home: homePowerScore,
        awayRaw: awayPowerScore,
        homeRaw: homePowerScore,
        higherIsBetter: true,
      },
      {
        label: "Power Play %",
        away: awayStanding.powerPlayPct != null ? `${(awayStanding.powerPlayPct * 100).toFixed(1)}%` : "—",
        home: homeStanding.powerPlayPct != null ? `${(homeStanding.powerPlayPct * 100).toFixed(1)}%` : "—",
        awayRaw: awayStanding.powerPlayPct ?? 0,
        homeRaw: homeStanding.powerPlayPct ?? 0,
        higherIsBetter: true,
      },
      {
        label: "Penalty Kill %",
        away: awayStanding.penaltyKillPct != null ? `${(awayStanding.penaltyKillPct * 100).toFixed(1)}%` : "—",
        home: homeStanding.penaltyKillPct != null ? `${(homeStanding.penaltyKillPct * 100).toFixed(1)}%` : "—",
        awayRaw: awayStanding.penaltyKillPct ?? 0,
        homeRaw: homeStanding.penaltyKillPct ?? 0,
        higherIsBetter: true,
      },
    ];
  }, [homeStanding, awayStanding, homePowerScore, awayPowerScore]);

  const formatGameDate = (dateStr: string) => {
    const date = new Date(dateStr + "T12:00:00");
    return new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric" }).format(date);
  };

  return (
    <div className="min-h-screen">
      <div className="container">
        {/* Back nav */}
        <div className="matchup-nav">
          <Link href="/predictions" className="matchup-nav__back">
            ← Back to predictions
          </Link>
          <div className="matchup-nav__info">
            <span>{formatGameDate(game.gameDate)}</span>
            <span className="matchup-nav__dot">·</span>
            <span>{game.startTimeEt ?? "TBD"}</span>
            {game.venue && (
              <>
                <span className="matchup-nav__dot">·</span>
                <span>{game.venue}</span>
              </>
            )}
          </div>
        </div>

        {/* Main matchup header - clean side by side */}
        <section className="matchup-header">
          <div className="matchup-header__team">
            <div className="matchup-header__crest" style={{ borderColor: awayColor }}>
              <TeamCrest abbrev={game.awayTeam.abbrev} size={88} />
            </div>
            <div className="matchup-header__info">
              <h1 className="matchup-header__name">{game.awayTeam.name}</h1>
              {awayStanding && (
                <p className="matchup-header__record">
                  {formatRecord(awayStanding)} <span className="matchup-header__rank">#{awayStanding.rank}</span>
                </p>
              )}
            </div>
          </div>

          <div className="matchup-header__center">
            <div className="matchup-header__probs">
              <span className="matchup-header__prob" style={{ color: awayColor }}>{pct(game.awayWinProb)}</span>
              <span className="matchup-header__vs">vs</span>
              <span className="matchup-header__prob" style={{ color: homeColor }}>{pct(game.homeWinProb)}</span>
            </div>
            <div className="matchup-header__bar">
              <div className="matchup-header__bar-fill" style={{ width: `${game.awayWinProb * 100}%`, background: awayColor }} />
              <div className="matchup-header__bar-fill" style={{ width: `${game.homeWinProb * 100}%`, background: homeColor }} />
            </div>
          </div>

          <div className="matchup-header__team matchup-header__team--right">
            <div className="matchup-header__info matchup-header__info--right">
              <h1 className="matchup-header__name">{game.homeTeam.name}</h1>
              {homeStanding && (
                <p className="matchup-header__record">
                  {formatRecord(homeStanding)} <span className="matchup-header__rank">#{homeStanding.rank}</span>
                </p>
              )}
            </div>
            <div className="matchup-header__crest" style={{ borderColor: homeColor }}>
              <TeamCrest abbrev={game.homeTeam.abbrev} size={88} />
            </div>
          </div>
        </section>

        {/* Model pick banner */}
        <section className="matchup-pick-banner">
          <div className="matchup-pick-banner__content">
            <div className="matchup-pick-banner__pick">
              <TeamCrest abbrev={favorite.abbrev} size={52} />
              <div>
                <p className="matchup-pick-banner__label">Model Pick</p>
                <p className="matchup-pick-banner__team">{favorite.name}</p>
              </div>
            </div>
            <div className="matchup-pick-banner__stats">
              <div className="matchup-pick-banner__stat">
                <span className="matchup-pick-banner__stat-value">{grade.label}</span>
                <span className="matchup-pick-banner__stat-label">Grade</span>
              </div>
              <div className="matchup-pick-banner__stat">
                <span className="matchup-pick-banner__stat-value">{edgePts.toFixed(1)}</span>
                <span className="matchup-pick-banner__stat-label">Edge</span>
              </div>
              <div className="matchup-pick-banner__stat">
                <span className="matchup-pick-banner__stat-value">{pct(favoriteProb)}</span>
                <span className="matchup-pick-banner__stat-label">Win %</span>
              </div>
            </div>
          </div>
          <p className="matchup-pick-banner__summary">{game.summary}</p>
        </section>

        {/* Team comparison stats */}
        {comparisonStats.length > 0 && (
          <section className="matchup-comparison">
            <div className="matchup-comparison__header">
              <div className="matchup-comparison__team">
                <TeamCrest abbrev={game.awayTeam.abbrev} size={40} />
                <span style={{ color: awayColor }}>{game.awayTeam.abbrev}</span>
              </div>
              <h2 className="matchup-comparison__title">Team Comparison</h2>
              <div className="matchup-comparison__team matchup-comparison__team--right">
                <span style={{ color: homeColor }}>{game.homeTeam.abbrev}</span>
                <TeamCrest abbrev={game.homeTeam.abbrev} size={40} />
              </div>
            </div>
            <div className="matchup-comparison__stats">
              {comparisonStats.map((stat) => (
                <StatBar
                  key={stat.label}
                  stat={stat}
                  awayColor={awayColor}
                  homeColor={homeColor}
                />
              ))}
            </div>
          </section>
        )}

        {/* Projected goalies */}
        {game.projectedGoalies && (game.projectedGoalies.home || game.projectedGoalies.away) && (
          <section className="matchup-goalies-section">
            <h3 className="matchup-section-title">Projected Goalies</h3>
            <div className="matchup-goalies-grid">
              {game.projectedGoalies.away && (
                <div className="matchup-goalie-card" style={{ borderColor: awayColor }}>
                  <div className="matchup-goalie-card__header">
                    <TeamCrest abbrev={game.awayTeam.abbrev} size={36} />
                    <span className="matchup-goalie-card__team">{game.awayTeam.abbrev}</span>
                  </div>
                  <p className="matchup-goalie-card__name">{game.projectedGoalies.away.name}</p>
                  <div className="matchup-goalie-card__stats">
                    <span>{game.projectedGoalies.away.record}</span>
                    <span>{game.projectedGoalies.away.restDays}d rest</span>
                  </div>
                </div>
              )}
              {game.projectedGoalies.home && (
                <div className="matchup-goalie-card" style={{ borderColor: homeColor }}>
                  <div className="matchup-goalie-card__header">
                    <TeamCrest abbrev={game.homeTeam.abbrev} size={36} />
                    <span className="matchup-goalie-card__team">{game.homeTeam.abbrev}</span>
                  </div>
                  <p className="matchup-goalie-card__name">{game.projectedGoalies.home.name}</p>
                  <div className="matchup-goalie-card__stats">
                    <span>{game.projectedGoalies.home.record}</span>
                    <span>{game.projectedGoalies.home.restDays}d rest</span>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Team page links */}
        <section className="matchup-links">
          <Link href={`/teams/${game.awayTeam.abbrev}`} className="matchup-link" style={{ borderColor: awayColor }}>
            <TeamCrest abbrev={game.awayTeam.abbrev} size={32} />
            <span>View {game.awayTeam.name}</span>
          </Link>
          <Link href={`/teams/${game.homeTeam.abbrev}`} className="matchup-link" style={{ borderColor: homeColor }}>
            <TeamCrest abbrev={game.homeTeam.abbrev} size={32} />
            <span>View {game.homeTeam.name}</span>
          </Link>
        </section>
      </div>
    </div>
  );
}
