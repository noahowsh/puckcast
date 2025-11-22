import Link from "next/link";
import type { ReactNode } from "react";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";
import { getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import { getPredictionGrade } from "@/lib/prediction";
import { teamBorderColor, teamGradient } from "@/lib/teamColors";

const modelInsights = insightsData as ModelInsights;
const predictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(predictionsPayload.games);
const liveSnapshots = buildTeamSnapshots();
const snapshotByAbbrev = new Map(liveSnapshots.map((team) => [team.abbrev, team]));
const standings = getCurrentStandings();

const powerIndex = standings
  .map((team) => {
    const overlay = snapshotByAbbrev.get(team.abbrev);
    return {
      ...team,
      record: `${team.wins}-${team.losses}-${team.ot}`,
      overlay,
      powerScore: computeStandingsPowerScore(team),
    };
  })
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => ({ ...team, powerRank: idx + 1, movement: team.rank - (idx + 1) }));

const topPower = powerIndex.slice(0, 5);
const biggestMover = powerIndex.reduce<PowerItem | null>((best, team) => {
  if (team.movement <= 0) return best;
  if (!best || team.movement > best.movement) return team;
  return best;
}, null);
const biggestSlider = powerIndex.reduce<PowerItem | null>((best, team) => {
  if (team.movement >= 0) return best;
  if (!best || team.movement < best.movement) return team;
  return best;
}, null);

const topEdges = todaysPredictions
  .slice()
  .sort((a, b) => Math.abs(b.edge) - Math.abs(a.edge))
  .slice(0, 3);

const upsetRadar = todaysPredictions
  .filter((g) => g.modelFavorite === "away" && g.awayWinProb >= 0.55)
  .sort((a, b) => b.awayWinProb - a.awayWinProb)
  .slice(0, 3);

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
const edgeGap = ((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1);
const updatedTimestamp = predictionsPayload.generatedAt ? new Date(predictionsPayload.generatedAt) : null;
const updatedDisplay = updatedTimestamp
  ? new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York",
      hour: "numeric",
      minute: "numeric",
      month: "short",
      day: "numeric",
    }).format(updatedTimestamp)
  : null;

type PowerItem = (typeof powerIndex)[number];

function Crest({ label }: { label: string }) {
  return (
    <span
      className="crest"
      style={{
        background: teamGradient(label),
        borderColor: teamBorderColor(label),
      }}
    >
      {label}
    </span>
  );
}

function EdgeMeter({ value }: { value: number }) {
  const width = Math.min(Math.abs(value) * 520, 100);
  const positive = value >= 0;
  return (
    <div className="edge-meter">
      <div
        className="edge-meter__fill"
        style={{ width: `${width}%`, background: positive ? "linear-gradient(90deg, #6ef0c2, #7ee3ff)" : "linear-gradient(90deg, #ff94a8, #f6c177)" }}
      />
    </div>
  );
}

function Pill({ children }: { children: ReactNode }) {
  return <span className="pill">{children}</span>;
}

export default function Home() {
  const heroStats = [
    { label: "Model accuracy", value: pct(modelInsights.overall.accuracy), detail: `+${edgeGap} pts vs baseline` },
    {
      label: "Slate ready",
      value: todaysPredictions.length ? `${todaysPredictions.length} games` : "Off-day",
      detail: updatedDisplay ? `Updated ${updatedDisplay} ET` : "Auto-refreshing",
    },
    { label: "Average edge", value: `${(modelInsights.overall.avgEdge * 100).toFixed(1)} pts`, detail: "Probability gap per matchup" },
  ];

  return (
    <div className="min-h-screen">
      <div className="container">
        <section className="nova-hero">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              {updatedDisplay && (
                <div className="pill-row">
                  <Pill>Live {updatedDisplay} ET</Pill>
                </div>
              )}
              <h1 className="display-xl">Predict the game before it&apos;s played.</h1>
              <p className="lead">
                Daily AI-powered win probabilities and power rankings built from real hockey data. Tested on thousands of NHL games with goalie
                form, travel, rink effects, and rest baked in.
              </p>
              <div className="cta-row">
                <Link href="/predictions" className="cta cta-primary">
                  View today&apos;s predictions
                </Link>
                <Link href="https://x.com/puckcastai" className="cta cta-ghost" target="_blank" rel="noreferrer">
                  Follow us for daily updates
                </Link>
              </div>
              <div className="stat-grid">
                {heroStats.map((stat) => (
                  <div key={stat.label} className="stat-tile">
                    <p className="stat-tile__label">{stat.label}</p>
                    <p className="stat-tile__value">{stat.value}</p>
                    <p className="stat-tile__detail">{stat.detail}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="nova-hero__panel">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">Tonight&apos;s signal</p>
                  <h3>Sharpest edges before puck drop</h3>
                </div>
              </div>

              <div className="edge-stack">
                {topEdges.length ? (
                  topEdges.map((game) => {
                    const favorite = game.modelFavorite === "home" ? game.homeTeam : game.awayTeam;
                    const prob = game.modelFavorite === "home" ? game.homeWinProb : game.awayWinProb;
                    const grade = getPredictionGrade(game.edge);
                    return (
                      <div key={game.id} className="edge-card edge-card--compact">
                        <div className="edge-card__header">
                          <div className="versus">
                            <Crest label={game.awayTeam.abbrev} />
                            <span className="versus__divider">@</span>
                            <Crest label={game.homeTeam.abbrev} />
                          </div>
                          <span className="tag">{game.startTimeEt ?? "TBD"}</span>
                        </div>
                        <div className="edge-card__body">
                          <div>
                            <p className="micro-label">Model lean</p>
                            <p className="edge-card__team">{favorite.name}</p>
                          </div>
                          <div className="edge-card__prob">
                            <span className="edge-card__prob-value">{pct(prob)}</span>
                            <span className="edge-card__grade">{grade.label}</span>
                          </div>
                        </div>
                        <EdgeMeter value={game.edge} />
                      </div>
                    );
                  })
                ) : (
                  <div className="empty-tile">
                    <p>No games on the slate today. The board will populate once the NHL schedule goes live.</p>
                  </div>
                )}
              </div>

              {upsetRadar.length > 0 && (
                <div className="upset-ribbon">
                  <p className="micro-label">Upset radar</p>
                  <div className="upset-grid">
                    {upsetRadar.map((game) => (
                      <div key={game.id} className="upset-card">
                        <div className="versus">
                          <Crest label={game.awayTeam.abbrev} />
                          <span className="versus__divider">at</span>
                          <Crest label={game.homeTeam.abbrev} />
                        </div>
                        <div className="upset-card__prob">
                          <span className="tag">Road lean</span>
                          <span className="edge-card__prob-value">{pct(game.awayWinProb)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="section-head">
            <div>
              <p className="eyebrow">Built for clarity</p>
              <h2>How Puckcast keeps you ahead</h2>
              <p className="lead-sm">Three pillars keep the signal tight: calibrated predictions, live drift tracking, and the weekly power index.</p>
            </div>
          </div>
          <div className="bento-grid">
            <div className="bento-card">
              <p className="micro-label">Game projections</p>
              <h3>Edge-first cards</h3>
              <p className="bento-copy">
                Every matchup shows the lean, win probability, edge bar, and grade. No scrolling for context—goalie form, rest, and travel already
                baked in.
              </p>
              <div className="pill-row">
                <Pill>Edge + grade</Pill>
                <Pill>Goalie &amp; rest baked in</Pill>
              </div>
            </div>
            <div className="bento-card bento-card--glow">
              <p className="micro-label">Live drift</p>
              <h3>Ticker for line moves</h3>
              <p className="bento-copy">
                Auto-refreshing feed surfaces probability shifts as lineups lock. See steam early and grab the number before it moves.
              </p>
              <div className="pill-row">
                <Pill>Lineup-aware</Pill>
                <Pill>Goalie confirmation</Pill>
              </div>
            </div>
            <div className="bento-card">
              <p className="micro-label">Power index</p>
              <h3>Who&apos;s real vs the standings</h3>
              <p className="bento-copy">
                Weekly blend of points, goal differential, and model win rate to spot risers and sliders before the standings catch up.
              </p>
              <div className="pill-row">
                <Pill>Movement calls</Pill>
                <Pill>Next opponent</Pill>
              </div>
            </div>
          </div>
        </section>

        <section className="nova-section">
          <div className="panel-split panel-split--tight">
            <div className="panel-split__copy">
              <div className="pill-row">
                <Pill>Puckcast Power Index</Pill>
                <Pill>Top 5 snapshot</Pill>
              </div>
              <h2>Puckcast Power Index</h2>
              <p className="lead-sm">
                Weekly blend of point pace, goal differential, and model win rate to surface who&apos;s outrunning their record—and who&apos;s living off luck.
              </p>
              <div className="power-facts">
                {biggestMover && (
                  <div className="power-fact">
                    <p className="micro-label">Biggest riser</p>
                    <p className="power-fact__value">{biggestMover.team}</p>
                    <p className="power-fact__detail">+{biggestMover.movement} spots</p>
                  </div>
                )}
                {biggestSlider && (
                  <div className="power-fact">
                    <p className="micro-label">Biggest slider</p>
                    <p className="power-fact__value">{biggestSlider.team}</p>
                    <p className="power-fact__detail">{biggestSlider.movement} spots</p>
                  </div>
                )}
              </div>
              <Link href="/leaderboards" className="cta cta-light">
                View full power board
              </Link>
            </div>

            <div className="power-list">
              {topPower.map((team) => (
                <PowerListItem key={team.abbrev} team={team} />
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function PowerListItem({ team }: { team: PowerItem }) {
  const movementDisplay = team.movement === 0 ? "Even" : team.movement > 0 ? `+${team.movement}` : `${team.movement}`;
  const movementTone = team.movement > 0 ? "movement--positive" : team.movement < 0 ? "movement--negative" : "movement--neutral";

  return (
    <div className="power-list-item">
      <div className="power-list-item__row">
        <div className="power-list-item__meta">
          <span className="power-rank">#{team.powerRank}</span>
          <span className="power-name">{team.team}</span>
          <Crest label={team.abbrev} />
        </div>
        <span className={`movement movement--pillless ${movementTone}`}>{movementDisplay}</span>
      </div>
      <div className="power-list-item__sub">
        <span className="chip-soft chip-soft--mini">Record {team.record}</span>
        <span className="chip-soft chip-soft--mini">Points {team.points}</span>
      </div>
    </div>
  );
}
