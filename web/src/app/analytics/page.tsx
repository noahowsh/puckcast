import insightsData from "@/data/modelInsights.json";
import type { DistributionFinding, FeatureImportance, ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const overview = modelInsights.overall;
const features = modelInsights.featureImportance;
const distributions = modelInsights.distributionFindings;
const confidenceBuckets = modelInsights.confidenceBuckets;
const strategies = modelInsights.strategies;
const teamPerformance = modelInsights.teamPerformance;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function AnalyticsPage() {
  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Deep analytics hub</p>
          <h1 className="text-4xl font-semibold text-white">Diagnostics from the archived 2023-24 audit.</h1>
          <p className="max-w-3xl text-base text-white/75">
            This view keeps the historical accuracy, feature importance, and calibration work accessible without distracting from
            the current-season experience.
          </p>
        </header>

        <section className="grid gap-6 md:grid-cols-2">
          <SummaryCard label="Accuracy" value={pct(overview.accuracy)} detail="Model hit rate vs actual results" />
          <SummaryCard label="Log loss" value={overview.logLoss.toFixed(3)} detail="Probability quality (lower is better)" />
          <SummaryCard label="Brier score" value={overview.brier.toFixed(3)} detail="Calibration error" />
          <SummaryCard label="Average edge" value={`${(overview.avgEdge * 100).toFixed(1)} pts`} detail="Mean |p - 0.5|" />
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Feature importance</p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {features.map((feature) => (
              <FeatureCard key={feature.feature} feature={feature} />
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <DistributionCard data={distributions} />
          <ConfidenceCard buckets={confidenceBuckets} />
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Strategy quick look</p>
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="text-white/60">
                <tr>
                  <th className="py-3 pr-4 text-left">Strategy</th>
                  <th className="py-3 px-4 text-left">Win %</th>
                  <th className="py-3 px-4 text-left">ROI / bet</th>
                  <th className="py-3 px-4 text-left">Units</th>
                  <th className="py-3 px-4 text-left">Bets</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {strategies.map((strategy) => (
                  <tr key={strategy.name}>
                    <td className="py-3 pr-4">
                      <p className="font-semibold text-white">{strategy.name}</p>
                      <p className="text-xs text-white/60">{strategy.note}</p>
                    </td>
                    <td className="py-3 px-4">{pct(strategy.winRate)}</td>
                    <td className="py-3 px-4">{((strategy.units / strategy.bets) * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</td>
                    <td className="py-3 px-4">{strategy.bets.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <p className="text-sm uppercase tracking-[0.4em] text-white/60">Holdout accuracy snapshot (2023-24)</p>
          <p className="mt-2 text-xs uppercase tracking-[0.4em] text-white/40">
            Used for auditing the model before the current 2025-26 deployment.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="text-white/60">
                <tr>
                  <th className="py-3 pr-4 text-left">Team</th>
                  <th className="py-3 px-4 text-left">Record</th>
                  <th className="py-3 px-4 text-left">Points</th>
                  <th className="py-3 px-4 text-left">Model hit %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {teamPerformance.map((team) => (
                  <tr key={team.team}>
                    <td className="py-3 pr-4">{team.team}</td>
                    <td className="py-3 px-4">{team.record}</td>
                    <td className="py-3 px-4">{team.points}</td>
                    <td className="py-3 px-4">{pct(team.modelAccuracy)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/20 p-5">
      <p className="text-xs uppercase tracking-[0.5em] text-white/60">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
      <p className="text-xs uppercase tracking-[0.4em] text-white/50">{detail}</p>
    </div>
  );
}

function FeatureCard({ feature }: { feature: FeatureImportance }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
      <p className="text-sm font-semibold text-white">{feature.feature}</p>
      <p className="text-xs uppercase tracking-[0.4em] text-white/50">
        Coefficient {feature.coefficient.toFixed(3)} · |impact| {feature.absImportance.toFixed(3)}
      </p>
    </article>
  );
}

function DistributionCard({ data }: { data: DistributionFinding[] }) {
  return (
    <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
      <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Distribution findings</p>
      <div className="mt-4 space-y-4">
        {data.map((entry) => (
          <article key={entry.metric} className="rounded-3xl border border-white/10 bg-black/20 p-4">
            <p className="text-xs uppercase tracking-[0.4em] text-white/60">{entry.metric}</p>
            <p className="mt-2 text-sm text-white/80">
              Correct avg {entry.correctMean.toFixed(3)} · Incorrect avg {entry.incorrectMean.toFixed(3)}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ConfidenceCard({ buckets }: { buckets: typeof confidenceBuckets }) {
  const intensity = (accuracy: number) => Math.min(Math.max((accuracy - 0.5) * 3, 0), 1);
  return (
    <section className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/40 via-slate-900/60 to-slate-950 p-8 shadow-2xl shadow-black/40">
      <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Confidence heat map</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {buckets.map((bucket) => {
          const strength = intensity(bucket.accuracy);
          const background = `linear-gradient(135deg, rgba(190,242,100,${0.25 + strength * 0.5}), rgba(34,197,94,${0.2 + strength * 0.5}))`;
          return (
            <article key={bucket.label} className="rounded-3xl border border-white/10 p-4" style={{ background }}>
              <p className="text-xs uppercase tracking-[0.4em] text-white/70">{bucket.label}</p>
              <p className="mt-2 text-3xl font-semibold text-white">{pct(bucket.accuracy)}</p>
              <p className="text-xs uppercase tracking-[0.4em] text-white/60">{bucket.count.toLocaleString()} samples</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
