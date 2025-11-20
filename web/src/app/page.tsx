import Link from "next/link";
import { PredictionCard } from "@/components/PredictionCard";
import { getGoaliePulse, getPredictionsPayload, selectCurrentSlate } from "@/lib/data";
import { PredictionTicker } from "@/components/PredictionTicker";
import { buildTeamSnapshots, computeStandingsPowerScore, getCurrentStandings } from "@/lib/current";
import standingsSnapshot from "@/data/currentStandings.json";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

type BankrollPoint = ModelInsights["bankrollSeries"][number];

const modelInsights = insightsData as ModelInsights;
const standingsMeta = standingsSnapshot as { generatedAt?: string };
const predictionsPayload = getPredictionsPayload();
const todaysPredictions = selectCurrentSlate(predictionsPayload.games);
const goaliePulse = getGoaliePulse();
const teamSnapshots = buildTeamSnapshots();
const snapshotByAbbrev = new Map(teamSnapshots.map((team) => [team.abbrev, team]));
const liveStandings = getCurrentStandings();
const topStandings = liveStandings.slice(0, 3);
const powerStandings = liveStandings
  .map((team) => {
    const overlay = snapshotByAbbrev.get(team.abbrev);
    return {
      ...team,
      record: `${team.wins}-${team.losses}-${team.ot}`,
      overlay,
      powerScore: computeStandingsPowerScore(team),
      nextGame: overlay?.nextGame,
    };
  })
  .sort((a, b) => b.powerScore - a.powerScore)
  .map((team, idx) => ({ ...team, powerRank: idx + 1, movement: team.rank - (idx + 1) }));
const powerLeaders = powerStandings.slice(0, 6);
const bankrollPreview = modelInsights.bankrollSeries.slice(-12);

const scheduleWindowDates = Array.from(new Set(predictionsPayload.games.map((game) => game.gameDate)))
  .filter((date): date is string => Boolean(date))
  .sort()
  .slice(0, 7);

type StressEntry = { team: string; abbrev: string; games: number };
const scheduleStressMap = new Map<string, StressEntry>();

const trackStress = (teamName: string, abbrev: string) => {
  if (!scheduleStressMap.has(abbrev)) {
    scheduleStressMap.set(abbrev, { team: teamName, abbrev, games: 0 });
  }
  scheduleStressMap.get(abbrev)!.games += 1;
};

predictionsPayload.games.forEach((game) => {
  if (!game.gameDate || !scheduleWindowDates.includes(game.gameDate)) return;
  trackStress(game.homeTeam.name, game.homeTeam.abbrev);
  trackStress(game.awayTeam.name, game.awayTeam.abbrev);
});

const scheduleStressLeaders = Array.from(scheduleStressMap.values())
  .sort((a, b) => b.games - a.games || a.team.localeCompare(b.team))
  .slice(0, 4);

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

const shortDateFormatter = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const formatShortDate = (iso?: string | null) => {
  if (!iso) return "TBD";
  return shortDateFormatter.format(new Date(`${iso}T00:00:00Z`));
};

const computeWeekStart = (anchor: Date) => {
  const base = new Date(anchor);
  const day = base.getUTCDay();
  const diff = (day + 6) % 7;
  base.setUTCDate(base.getUTCDate() - diff);
  base.setUTCHours(0, 0, 0, 0);
  return base;
};

const weeklyAnchor = standingsMeta.generatedAt ? new Date(standingsMeta.generatedAt) : updatedTimestamp ?? new Date();
const weekStartDate = computeWeekStart(weeklyAnchor);
const weekStartDisplay = shortDateFormatter.format(weekStartDate);

const methodology = [
  {
    title: "Data ingestion",
    detail: "MoneyPuck, NHL play-by-play, micro-stat partners, and our own goalie tracking feed join a unified warehouse.",
  },
  {
    title: "Feature engineering",
    detail: "Game state-adjusted xG, rest/altitude modifiers, line chemistry trends, and coaching pace fingerprints.",
  },
  {
    title: "Simulation layer",
    detail: "Gradient boosted win-prob core runs 50k Monte Carlo sims per matchup with lineup + goalie uncertainty baked in.",
  },
  {
    title: "Distribution outputs",
    detail: "We expose win %, puck line cover odds, total goal distributions, and derivative signals for props.",
  },
];

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const commandCenterStats = [
  { label: "Games tracked", value: modelInsights.overall.games.toLocaleString(), detail: "2025-26 to date" },
  { label: "Model accuracy", value: pct(modelInsights.overall.accuracy), detail: "vs actual results" },
  { label: "Home baseline", value: pct(modelInsights.overall.baseline), detail: "Always pick home" },
  { label: "Brier score", value: modelInsights.overall.brier.toFixed(3), detail: "Probability calibration" },
];

const performanceReceipts = [
  {
    title: "Accuracy lift",
    stat: `+${((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1)} pts`,
    detail: `${pct(modelInsights.overall.accuracy)} vs ${pct(modelInsights.overall.baseline)} baseline`,
  },
  {
    title: "Log loss",
    stat: modelInsights.overall.logLoss.toFixed(3),
    detail: "lower is better",
  },
  {
    title: "Average edge",
    stat: `${(modelInsights.overall.avgEdge * 100).toFixed(1)} pts`,
    detail: "probability delta vs 50/50",
  },
];

const heroHighlights = [
  { label: "Season focus", value: "2025-26", detail: "Nightly sync" },
  { label: "Games tracked", value: modelInsights.overall.games.toLocaleString(), detail: "live sample" },
  {
    label: "Accuracy lift",
    value: `+${((modelInsights.overall.accuracy - modelInsights.overall.baseline) * 100).toFixed(1)} pts`,
    detail: "vs home baseline",
  },
];

const weeklyAccuracyMetrics = [
  {
    label: "Model accuracy",
    value: pct(modelInsights.overall.accuracy),
    detail: "Week of " + weekStartDisplay,
    progress: modelInsights.overall.accuracy,
  },
  {
    label: "Baseline",
    value: pct(modelInsights.overall.baseline),
    detail: "Always pick home",
    progress: modelInsights.overall.baseline,
  },
  {
    label: "Avg edge",
    value: `${(modelInsights.overall.avgEdge * 100).toFixed(1)} pts`,
    detail: "Mean |p-0.5|",
    progress: Math.min(modelInsights.overall.avgEdge * 2, 1),
  },
];

const confidenceBuckets = modelInsights.confidenceBuckets.map((bucket) => ({
  range: bucket.label,
  accuracy: bucket.accuracy,
  sample: bucket.count,
  status:
    bucket.accuracy >= 0.65 ? "Excellent" : bucket.accuracy >= 0.6 ? "Great" : bucket.accuracy >= 0.55 ? "Improving" : "Needs review",
}));

const featureHighlights = modelInsights.featureImportance.slice(0, 3);
const distributionInsights = modelInsights.distributionFindings;
const gradeLegend = [
  { label: "A+", detail: "≥20 pts edge · rare conviction" },
  { label: "A", detail: "17-19 pts edge · heavy lean" },
  { label: "A-", detail: "14-16 pts edge · high leverage" },
  { label: "B+", detail: "10-13 pts edge · meaningful signal" },
  { label: "B", detail: "7-9 pts edge · steady lean" },
  { label: "B-", detail: "4-6 pts edge · slight lean" },
  { label: "C+", detail: "2-3 pts edge · marginal" },
  { label: "C", detail: "<2 pts edge · coin flip" },
];
const insightCards = modelInsights.insights.slice(0, 3);
const navPreviewCards = [
  {
    title: "Predictions",
    href: "/predictions",
    summary: `${todaysPredictions.length} games live`,
    detail: "Edge-coded matchup cards + ticker",
    tag: "Slate",
  },
  {
    title: "Betting",
    href: "/betting",
    summary: `${modelInsights.strategies.length} thresholds tested`,
    detail: "Edge slider, bankroll curve, definitions",
    tag: "Sandbox",
  },
  {
    title: "Leaderboards",
    href: "/leaderboards",
    summary: "32 clubs ranked nightly",
    detail: "Power rankings vs actual standings",
    tag: "Power",
  },
  {
    title: "Analytics",
    href: "/analytics",
    summary: `${modelInsights.featureImportance.length}+ diagnostics`,
    detail: "Feature importance + calibration",
    tag: "Research",
  },
  {
    title: "Goalies",
    href: "/goalies",
    summary: `${goaliePulse.goalies.length} goalies tracked`,
    detail: goaliePulse.goalies[0] ? `${goaliePulse.goalies[0].name} trending ${goaliePulse.goalies[0].trend}` : "Start odds ticker",
    tag: "Start odds",
  },
];

export default function Home() {
  return (
    <div className="relative overflow-hidden">
      <BackgroundGlow />
      <div className="relative z-10 mx-auto flex max-w-6xl flex-col gap-20 px-6 pb-12 pt-6 lg:px-12">
        <main className="space-y-24">
          <section className="rounded-[42px] border border-white/10 bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-950/80 p-8 shadow-2xl shadow-black/40 space-y-6">
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)] lg:items-start">
              <div className="space-y-6">
                <div className="space-y-4">
                  <p className="text-sm uppercase tracking-[0.5em] text-lime-300">AI-Powered NHL Predictions</p>
                  <h1 className="text-4xl font-semibold text-white sm:text-5xl">
                    Know the outcome before <span className="bg-gradient-to-r from-lime-300 via-emerald-400 to-cyan-300 bg-clip-text text-transparent">puck drop.</span>
                  </h1>
                  <p className="text-base text-white/80">
                    Machine learning meets hockey analytics. Daily win probabilities with A-C confidence grades, power rankings that actually matter,
                    and transparent model insights — updated every morning at 10am ET with fresh goalie confirmations and injury reports.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Link
                      href="https://x.com/puckcastai"
                      target="_blank"
                      className="rounded-full bg-gradient-to-r from-lime-300 to-emerald-400 px-6 py-3 text-sm font-semibold uppercase tracking-wider text-slate-950 shadow-lg shadow-emerald-500/30 transition hover:shadow-emerald-400/40"
                    >
                      Follow daily updates
                    </Link>
                    <Link
                      href="#methodology"
                      className="rounded-full border border-white/20 px-6 py-3 text-sm font-semibold uppercase tracking-wider text-white/80 transition hover:text-white"
                    >
                      How it works
                    </Link>
                  </div>
                  <p className="text-sm uppercase tracking-[0.4em] text-white/50">
                    {updatedDisplay ? `Synced ${updatedDisplay} ET` : "Awaiting next model run"}
                  </p>
                </div>
                <div className="rounded-[24px] border border-white/10 bg-white/5 p-4 text-white/80">
                  <p className="text-xs uppercase tracking-[0.4em] text-white/50">Daily Predictions · Week of {weekStartDisplay}</p>
                  <p className="mt-1 text-sm">
                    Every game gets a win probability and confidence grade (A+ to C). A+ means ≥20 pts edge — near lock territory.
                    C means coin flip. Predictions sync daily at 10am ET after goalie confirmations and injury reports drop.
                  </p>
                </div>
                <div className="grid gap-4 border-y border-white/10 py-6 text-white/80 sm:grid-cols-3">
                  {heroHighlights.map((stat) => (
                    <div key={stat.label}>
                      <p className="text-xs uppercase tracking-[0.3em] text-white/50">{stat.label}</p>
                      <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
                      <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/60">{stat.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex justify-center lg:justify-end">
                <div className="w-full max-w-sm rounded-[32px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/40 backdrop-blur space-y-5">
                  <div>
                    <p className="text-sm uppercase tracking-[0.5em] text-white/60">Season pulse · Week of {weekStartDisplay}</p>
                    <p className="text-lg text-white/80">Top three clubs by live standings</p>
                  </div>
                  <div className="space-y-3">
                    {topStandings.map((team, index) => (
                      <div key={team.abbrev} className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                        <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/50">
                          <span>#{index + 1} · {team.gamesPlayed} gp</span>
                          <span>{team.points} pts</span>
                        </div>
                        <p className="mt-1 text-lg font-semibold text-white">{team.team}</p>
                        <p className="text-xs text-white/70">
                          {team.wins}-{team.losses}-{team.ot} · Diff {team.goalDifferential >= 0 ? "+" : ""}
                          {team.goalDifferential}
                        </p>
                      </div>
                    ))}
                  </div>
                  <div className="rounded-2xl bg-gradient-to-r from-lime-300/20 to-emerald-400/20 p-4 text-sm text-white/80">
                    Updated every morning at 10am ET after skate reports, goalie confirmations, and roster notes settle.
                  </div>
                </div>
              </div>
            </div>
            <PredictionTicker initial={predictionsPayload} />
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[36px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30">
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Weekly accuracy tracker</p>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                {weeklyAccuracyMetrics.map((metric) => (
                  <div key={metric.label} className="rounded-2xl border border-white/10 bg-black/20 p-4">
                    <p className="text-xs uppercase tracking-[0.4em] text-white/50">{metric.label}</p>
                    <p className="mt-2 text-2xl font-semibold text-white">{metric.value}</p>
                    <p className="text-[0.6rem] uppercase tracking-[0.4em] text-white/60">{metric.detail}</p>
                    <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-lime-300 via-emerald-400 to-cyan-300"
                        style={{ width: `${Math.min(metric.progress * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/30 via-slate-900/60 to-slate-950 p-6 shadow-2xl shadow-black/30">
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Schedule stress meter</p>
              <p className="mt-2 text-sm text-white/70">Busiest slates over the next week (model input window)</p>
              <ul className="mt-5 space-y-3">
                {scheduleStressLeaders.length ? (
                  scheduleStressLeaders.map((entry) => (
                    <li key={entry.abbrev} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                      <div className="flex items-center justify-between text-sm text-white/80">
                        <span>{entry.team}</span>
                        <span className="text-xs uppercase tracking-[0.4em] text-lime-200">{entry.games} games</span>
                      </div>
                      <p className="text-xs uppercase tracking-[0.4em] text-white/40">Week of {weekStartDisplay}</p>
                    </li>
                  ))
                ) : (
                  <li className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                    Schedule data not available yet.
                  </li>
                )}
              </ul>
            </div>
          </section>

          <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Signal notes</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Quick context pulled from the latest model run.</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {insightCards.map((insight) => (
                <article key={insight.title} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-semibold text-white">{insight.title}</p>
                  <p className="mt-2 text-sm text-white/80">{insight.detail}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="predictions" className="space-y-10">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Tonight&apos;s Predictions</p>
                <h2 className="text-3xl font-semibold text-white">Every game graded A+ to C based on confidence.</h2>
              <p className="mt-2 max-w-2xl text-base text-white/75">
                Win probabilities backed by 6 seasons of data, 200+ engineered features, and real-time goalie confirmations.
                A+ games (≥20 pts edge) are model slam dunks. C games (&lt;2 pts edge) are true coin flips.
              </p>
            </div>
            <p className="text-sm text-white/60">
                {updatedDisplay ? `Last refreshed ${updatedDisplay} ET` : "Waiting on the next publish window."}
            </p>
          </div>
            <div className="grid grid-cols-2 gap-3 rounded-[28px] border border-white/10 bg-white/5 p-4 text-xs uppercase tracking-[0.4em] text-white/60 sm:grid-cols-4">
              {gradeLegend.map((grade) => (
                <div key={grade.label}>
                  <p className="text-white">{grade.label}</p>
                  <p className="mt-1 text-[0.55rem] text-white/60 normal-case tracking-normal">{grade.detail}</p>
                </div>
              ))}
            </div>
            {todaysPredictions.length > 0 ? (
              <div className="grid gap-6 md:grid-cols-2">
                {todaysPredictions.map((prediction) => (
                  <PredictionCard key={prediction.id} prediction={prediction} />
                ))}
              </div>
            ) : (
              <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-center text-white/70">
                <p>No future games available yet. Check back once the league posts the next slate.</p>
              </div>
            )}
          </section>

          <section className="rounded-[40px] border border-white/10 bg-gradient-to-br from-white/5 via-slate-900/40 to-slate-950 p-10 shadow-2xl shadow-black/40">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Model health</p>
                <h2 className="mt-3 text-3xl font-semibold text-white">Season-long vitals at a glance.</h2>
                <p className="mt-2 max-w-3xl text-base text-white/80">
                  Snapshot of sample size, calibration, and edge quality. Everything updates alongside the same nightly run that
                  powers the other tabs.
                </p>
              </div>
            </div>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {commandCenterStats.map((stat) => (
                <div key={stat.label} className="rounded-3xl border border-white/10 bg-black/30 p-4">
                  <p className="text-xs uppercase tracking-[0.4em] text-white/50">{stat.label}</p>
                  <p className="mt-3 text-2xl font-semibold text-white">{stat.value}</p>
                  <p className="text-xs uppercase tracking-[0.4em] text-white/60">{stat.detail}</p>
                </div>
              ))}
            </div>
            <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  {performanceReceipts.map((receipt) => (
                    <div
                      key={receipt.title}
                      className="rounded-3xl border border-lime-200/30 bg-gradient-to-br from-lime-200/10 via-emerald-200/0 to-transparent p-5"
                    >
                      <p className="text-xs uppercase tracking-[0.5em] text-white/60">{receipt.title}</p>
                      <p className="mt-3 text-3xl font-semibold text-white">{receipt.stat}</p>
                      <p className="text-sm text-white/80">{receipt.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-[30px] border border-white/10 bg-black/30 p-5">
                <p className="text-xs uppercase tracking-[0.4em] text-white/60">Bankroll trace</p>
                <p className="mt-2 text-sm text-white/70">Even-money assumption · audit sample</p>
                <div className="mt-4">
                  <BankrollSparkline points={bankrollPreview} />
                </div>
              </div>
            </div>
          </section>

          <section id="tabs" className="space-y-8">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Site modules</p>
                <h2 className="text-3xl font-semibold text-white">Every dashboard view now lives natively on the site.</h2>
                <p className="mt-2 max-w-3xl text-base text-white/75">
                  Pick a tab to dive into the detailed view—no separate dashboard required. Each preview pulls real counts from the
                  current data drop.
                </p>
              </div>
              <p className="text-xs uppercase tracking-[0.4em] text-white/50">Predictions · Betting · Leaderboards · Analytics · Goalies</p>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              {navPreviewCards.map((module) => (
                <article
                  key={module.title}
                  className="rounded-[32px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30 transition hover:-translate-y-1 hover:border-lime-200/50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.4em] text-white">{module.title}</p>
                      <p className="mt-2 text-sm text-white/70">{module.summary}</p>
                    </div>
                    <span className="rounded-full border border-white/20 px-3 py-1 text-[0.6rem] uppercase tracking-[0.4em] text-white/70">
                      {module.tag}
                    </span>
                  </div>
                  <p className="mt-4 text-sm text-white/80">{module.detail}</p>
                  <Link
                    href={module.href}
                    className="mt-6 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.4em] text-lime-200"
                  >
                    Open {module.title}
                    <span aria-hidden>→</span>
                  </Link>
                </article>
              ))}
            </div>
          </section>

          <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Power pulse</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Top clubs by the live power ranking formula.</h2>
              <p className="mt-2 text-sm text-white/70">Points, goal differential, tempo, and shot share roll into one nightly score.</p>
              <ul className="mt-6 space-y-4">
                {powerLeaders.map((team) => {
                  const overlay = team.overlay;
                  return (
                    <li key={team.abbrev} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                      <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/50">
                        <span>
                          #{team.powerRank} power ·
                          {team.movement === 0 ? " In sync" : team.movement > 0 ? ` +${team.movement}` : ` -${Math.abs(team.movement)}`}
                        </span>
                        <span>Standings #{team.rank}</span>
                      </div>
                      <p className="mt-2 text-lg font-semibold text-white">{team.team}</p>
                      <p className="text-sm text-white/70">
                        {team.record} · {team.points} pts
                      </p>
                      <div className="mt-3 grid gap-3 text-xs uppercase tracking-[0.3em] text-white/50 sm:grid-cols-3">
                        <span>
                          {team.goalDifferential >= 0 ? "+" : ""}
                          {team.goalDifferential} goal diff
                        </span>
                        <span>{pct(team.pointPctg)} pts pct</span>
                        <span>
                          {overlay
                            ? `${pct(overlay.avgProb)} model win`
                            : `${(team.goalsForPerGame ?? 0).toFixed(1)} gf/g`}
                        </span>
                      </div>
                      <p className="mt-3 text-xs uppercase tracking-[0.4em] text-white/40">
                        {team.nextGame
                          ? `Next: ${team.nextGame.opponent} · ${formatShortDate(team.nextGame.date)} · ${team.nextGame.startTimeEt ?? "TBD"}`
                          : "Next game TBD"}
                      </p>
                    </li>
                  );
                })}
              </ul>
            </div>
            <div className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/40 via-slate-900/60 to-slate-950 p-8 shadow-2xl shadow-black/40">
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Confidence buckets</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Calibration view exported straight from the Performance tab.</h2>
              <div className="mt-6 space-y-4">
                {confidenceBuckets.map((bucket) => {
                  const accuracyDisplay = `${Math.round(bucket.accuracy * 100)}%`;
                  return (
                    <div key={bucket.range} className="rounded-3xl border border-white/10 bg-white/5 p-4">
                      <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/60">
                        <span>{bucket.range}</span>
                        <span className="text-white/80">{bucket.status}</span>
                      </div>
                      <div className="mt-3 flex items-baseline justify-between">
                        <p className="text-3xl font-semibold text-white">{accuracyDisplay}</p>
                        <p className="text-xs uppercase tracking-[0.4em] text-white/50">{bucket.sample.toLocaleString()} samples</p>
                      </div>
                      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-lime-300 via-emerald-400 to-cyan-300"
                          style={{ width: `${bucket.accuracy * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="rounded-[36px] border border-white/10 bg-white/5 p-10 shadow-2xl shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Deep analysis</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Feature importance + sample diagnostics from the latest run.</h2>
            <div className="mt-8 grid gap-8 md:grid-cols-2">
              <div className="space-y-4">
                <p className="text-xs uppercase tracking-[0.5em] text-white/60">Top coefficients</p>
                {featureHighlights.map((feature) => (
                  <article key={feature.feature} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                    <p className="text-sm font-semibold text-white">{feature.feature}</p>
                    <p className="text-xs uppercase tracking-[0.4em] text-white/50">
                      Coefficient {feature.coefficient.toFixed(3)} · |impact| {feature.absImportance.toFixed(3)}
                    </p>
                  </article>
                ))}
              </div>
              <div className="space-y-4">
                <p className="text-xs uppercase tracking-[0.5em] text-white/60">Context stats</p>
                {distributionInsights.map((entry) => (
                  <article key={entry.metric} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                    <p className="text-sm font-semibold text-white">{entry.metric}</p>
                    <p className="mt-2 text-sm text-white/80">
                      Correct avg {entry.correctMean.toFixed(3)} · Incorrect avg {entry.incorrectMean.toFixed(3)}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section id="methodology" className="rounded-[40px] border border-white/10 bg-white/5 p-10 shadow-inner shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Stack</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Built for reliability + transparent storytelling.</h2>
            <div className="mt-8 grid gap-8 md:grid-cols-2">
              {methodology.map((step) => (
                <div key={step.title} className="rounded-3xl border border-white/10 bg-black/20 p-6">
                  <p className="text-xs uppercase tracking-[0.5em] text-white/60">{step.title}</p>
                  <p className="mt-3 text-base leading-relaxed text-white/80">{step.detail}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[36px] border border-lime-200/30 bg-gradient-to-br from-lime-200/20 via-emerald-200/20 to-transparent p-10 text-center shadow-lg shadow-emerald-500/20">
            <p className="text-sm uppercase tracking-[0.5em] text-lime-200">Stay close</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Nightly summaries land on X first.</h2>
            <p className="mt-3 text-base text-white/80">
              Follow @puckcast for quick cards on slate changes, goalie confirmations, and any notable model swings.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="https://x.com/puckcastai"
                target="_blank"
                className="rounded-full bg-white px-8 py-3 text-sm font-semibold uppercase tracking-[0.4em] text-slate-900 shadow-lg shadow-slate-900/10"
              >
                Follow @puckcastai
              </Link>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function BackgroundGlow() {
  return (
    <div className="pointer-events-none absolute inset-0">
      <div className="absolute -left-40 top-[-120px] h-72 w-72 rounded-full bg-emerald-400/30 blur-3xl" />
      <div className="absolute right-[-80px] top-10 h-96 w-96 rounded-full bg-lime-300/20 blur-[140px]" />
      <div className="absolute inset-x-0 bottom-0 h-64 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent" />
    </div>
  );
}

function BankrollSparkline({ points }: { points: BankrollPoint[] }) {
  if (!points.length) {
    return <p className="text-sm text-white/60">No bankroll history available.</p>;
  }
  const max = Math.max(...points.map((point) => point.units));
  const min = Math.min(...points.map((point) => point.units));
  const span = Math.max(points.length - 1, 1);
  const normalized = points.map((point, idx) => ({
    x: (idx / span) * 100,
    y: max === min ? 50 : ((point.units - min) / (max - min)) * 100,
  }));
  const path = normalized
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${100 - point.y}`)
    .join(" ");

  return (
    <>
      <svg viewBox="0 0 100 100" className="h-32 w-full">
        <path d={path} fill="none" stroke="url(#bankrollMini)" strokeWidth="2.5" strokeLinecap="round" />
        <defs>
          <linearGradient id="bankrollMini" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#bef264" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
        </defs>
      </svg>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs uppercase tracking-[0.3em] text-white/50">
        {points.slice(-4).map((point) => (
          <div key={point.label} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-center">
            <p className="text-white/70">{point.label}</p>
            <p className="text-white">{point.units.toFixed(0)}u</p>
          </div>
        ))}
      </div>
    </>
  );
}
