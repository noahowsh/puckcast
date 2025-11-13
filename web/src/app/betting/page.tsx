"use client";

import { useMemo, useState, type ReactNode } from "react";
import insightsData from "@/data/modelInsights.json";
import type { BankrollPoint, ModelInsights, StrategySummary } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const strategies = modelInsights.strategies;
const bankrollSeries = modelInsights.bankrollSeries;
const sortedStrategies = [...strategies].sort((a, b) => b.units - a.units);
const strategyLeaders = sortedStrategies.slice(0, 2);
const strategyLaggards = sortedStrategies.slice(-2).reverse();

const edgeOptions = [0, 5, 10, 15];

function edgeFromName(name: string) {
  const match = name.match(/(\d+)\s*pts/);
  return match ? parseInt(match[1], 10) : 0;
}

const strategyByEdge = strategies.reduce<Record<number, StrategySummary>>((acc, strategy) => {
  acc[edgeFromName(strategy.name)] = strategy;
  return acc;
}, {});

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function BettingPage() {
  const [edgeThreshold, setEdgeThreshold] = useState(10);

  const activeStrategy = useMemo(() => {
    const closest = edgeOptions.reduce((prev, curr) =>
      Math.abs(curr - edgeThreshold) < Math.abs(prev - edgeThreshold) ? curr : prev,
    edgeOptions[0]);
    return strategyByEdge[closest] ?? strategies[0];
  }, [edgeThreshold]);

  const roiPerBet = ((activeStrategy.units / activeStrategy.bets) * 100).toFixed(1);

  return (
    <div className="relative overflow-hidden">
      <div className="relative mx-auto flex max-w-6xl flex-col gap-12 px-6 pb-16 pt-8 lg:px-12">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Betting lab</p>
          <h1 className="text-4xl font-semibold text-white">Interactive strategy sandbox for the live model.</h1>
          <p className="max-w-3xl text-base text-white/75">
            Move the edge slider to see how win rate, ROI, and units respond. Stats are grounded in the archived 2023-24 backtest,
            while the slider thresholds mirror tonight&apos;s probabilities.
          </p>
        </header>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-white/50">Edge threshold</p>
              <h2 className="text-2xl font-semibold text-white">Filter simulations by minimum probability edge.</h2>
            </div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">0 pts = every prediction</p>
          </div>
          <div className="mt-6 space-y-4">
            <input
              type="range"
              min="0"
              max="15"
              step="5"
              value={edgeThreshold}
              onChange={(event) => setEdgeThreshold(Number(event.target.value))}
              className="w-full accent-lime-300"
            />
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-white/60">
              {edgeOptions.map((value) => (
                <span key={value}>{value} pts</span>
              ))}
            </div>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            <SummaryCard label="Win rate" value={pct(activeStrategy.winRate)} detail={`${activeStrategy.bets.toLocaleString()} bets`} />
            <SummaryCard label="ROI / bet" value={`${roiPerBet}%`} detail="even-money assumption" />
            <SummaryCard label="Units" value={`${activeStrategy.units > 0 ? "+" : ""}${activeStrategy.units}u`} detail="wins - losses" />
            <SummaryCard label="Avg edge" value={`${(activeStrategy.avgEdge * 100).toFixed(1)} pts`} detail="mean |p-0.5|" />
          </div>
          <p className="mt-4 text-xs text-white/60">{activeStrategy.note}</p>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Weekly edge recap</p>
            <p className="mt-2 text-sm text-white/70">Strategies adding the most units this season-to-date.</p>
            <div className="mt-6 space-y-4">
              {strategyLeaders.map((strategy) => (
                <div key={strategy.name} className="rounded-3xl border border-white/10 bg-black/20 p-4">
                  <p className="text-sm font-semibold text-white">{strategy.name}</p>
                  <p className="text-xs uppercase tracking-[0.4em] text-white/50">{strategy.note}</p>
                  <div className="mt-3 flex items-center justify-between text-white">
                    <span className="text-2xl font-semibold">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</span>
                    <span className="text-sm text-lime-200">{pct(strategy.winRate)} hit rate</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
            <p className="text-sm uppercase tracking-[0.4em] text-white/60">Under construction</p>
            <p className="mt-2 text-sm text-white/70">Strategies currently lagging provide context for variance.</p>
            <div className="mt-6 space-y-4">
              {strategyLaggards.map((strategy) => (
                <div key={strategy.name} className="rounded-3xl border border-white/10 bg-black/10 p-4">
                  <p className="text-sm font-semibold text-white">{strategy.name}</p>
                  <div className="mt-3 flex items-center justify-between text-white">
                    <span className="text-2xl font-semibold text-rose-200">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</span>
                    <span className="text-sm text-white/60">{strategy.bets.toLocaleString()} bets</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[36px] border border-white/10 bg-gradient-to-br from-black/30 via-slate-900/60 to-slate-950 p-8 shadow-2xl shadow-black/40">
            <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Bankroll curve</p>
            <h2 className="text-2xl font-semibold text-white">All-picks cumulative units.</h2>
            <div className="mt-6">
              <Sparkline points={bankrollSeries} />
            </div>
            <p className="mt-4 text-sm text-white/70">+168 units from opening night through April 18 (even-money assumption).</p>
          </div>
          <div className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30 space-y-4">
            <p className="text-sm uppercase tracking-[0.4em] text-white/60">Term guide</p>
            <Definition term="Edge">
              Absolute difference between the model&apos;s win probability and a 50/50 coin flip. 10 pts = 60% vs 50%.
            </Definition>
            <Definition term="Units">
              One unit equals one stake in the backtest. Positive units means more wins than losses at even odds.
            </Definition>
            <Definition term="ROI per bet">
              Average return per wager (wins minus losses divided by total bets). Even-money assumption simplifies the math.
            </Definition>
          </div>
        </section>

        <section className="rounded-[36px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/30">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-lime-300">Strategy board</p>
              <h2 className="text-2xl font-semibold text-white">How each threshold behaved in the audit season.</h2>
            </div>
            <p className="text-xs uppercase tracking-[0.4em] text-white/40">All figures assume even-money pricing</p>
          </div>
          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="text-white/60">
                <tr>
                  <th className="py-3 pr-4 text-left">Edge gate</th>
                  <th className="py-3 px-4 text-left">Win %</th>
                  <th className="py-3 px-4 text-left">ROI / bet</th>
                  <th className="py-3 px-4 text-left">Units</th>
                  <th className="py-3 px-4 text-left">Samples</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {strategies.map((strategy) => (
                  <tr key={strategy.name}>
                    <td className="py-3 pr-4 font-semibold text-white">{strategy.name}</td>
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

function Definition({ term, children }: { term: string; children: ReactNode }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-black/20 p-4">
      <p className="text-xs uppercase tracking-[0.4em] text-white/60">{term}</p>
      <p className="mt-2 text-sm text-white/80">{children}</p>
    </article>
  );
}

function Sparkline({ points }: { points: BankrollPoint[] }) {
  if (points.length === 0) {
    return <div className="text-sm text-white/60">No bankroll history available.</div>;
  }
  const max = Math.max(...points.map((p) => p.units));
  const min = Math.min(...points.map((p) => p.units));
  const divisor = Math.max(points.length - 1, 1);
  const normalized = points.map((p, idx) => ({
    x: (idx / divisor) * 100,
    y: ((p.units - min) / (max - min || 1)) * 100,
  }));
  const path = normalized
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${100 - point.y}`)
    .join(" ");

  return (
    <div>
      <svg viewBox="0 0 100 100" className="h-48 w-full">
        <path d={path} fill="none" stroke="url(#bankroll)" strokeWidth="2" strokeLinecap="round" />
        <defs>
          <linearGradient id="bankroll" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#bef264" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
        </defs>
      </svg>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs uppercase tracking-[0.3em] text-white/50">
        {points.slice(-4).map((point) => (
          <div key={point.label} className="rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-center">
            <p className="text-white/70">{point.label}</p>
            <p className="text-white">{point.units.toFixed(0)}u</p>
          </div>
        ))}
      </div>
    </div>
  );
}
