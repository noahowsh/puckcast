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
    <div className="relative min-h-screen bg-slate-950">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-sky-950/20 via-slate-950 to-slate-950" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6 py-16 lg:px-8">
        {/* Header */}
        <section className="mb-32">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3 py-1">
            <span className="text-xs font-medium text-sky-400">Betting Lab</span>
          </div>
          <h1 className="mb-8 text-6xl font-extrabold text-white lg:text-7xl">Interactive strategy sandbox</h1>
          <p className="max-w-3xl text-xl text-slate-300">
            Adjust the edge slider to see how win rate, ROI, and units respond. Stats are based on the 2023-24 backtest archive.
          </p>
        </section>

        {/* Edge Slider */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <h2 className="text-2xl font-extrabold text-white">Edge Threshold</h2>
                <p className="mt-1 text-sm text-slate-400">Filter by minimum probability edge</p>
              </div>
              <p className="text-sm text-slate-500">0 pts = every prediction</p>
            </div>
            <div className="space-y-4">
              <input
                type="range"
                min="0"
                max="15"
                step="5"
                value={edgeThreshold}
                onChange={(event) => setEdgeThreshold(Number(event.target.value))}
                className="w-full accent-sky-500"
              />
              <div className="flex items-center justify-between text-sm text-slate-400">
                {edgeOptions.map((value) => (
                  <span key={value}>{value} pts</span>
                ))}
              </div>
            </div>
            <div className="mt-6 grid gap-8 md:grid-cols-4">
              <SummaryCard label="Win rate" value={pct(activeStrategy.winRate)} detail={`${activeStrategy.bets.toLocaleString()} bets`} />
              <SummaryCard label="ROI / bet" value={`${roiPerBet}%`} detail="even-money assumption" />
              <SummaryCard label="Units" value={`${activeStrategy.units > 0 ? "+" : ""}${activeStrategy.units}u`} detail="wins - losses" />
              <SummaryCard label="Avg edge" value={`${(activeStrategy.avgEdge * 100).toFixed(1)} pts`} detail="mean |p-0.5|" />
            </div>
            <p className="mt-4 text-sm text-slate-400">{activeStrategy.note}</p>
          </div>
        </section>

        {/* Strategy Leaders */}
        <section className="mb-32">
          <div className="grid gap-8 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <h2 className="mb-4 text-2xl font-extrabold text-white">Top Performers</h2>
              <p className="mb-8 text-sm text-slate-400">Strategies adding the most units this season</p>
              <div className="space-y-4">
                {strategyLeaders.map((strategy) => (
                  <div key={strategy.name} className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
                    <p className="font-semibold text-white">{strategy.name}</p>
                    <p className="mt-1 text-xs text-slate-500">{strategy.note}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-2xl font-bold text-white">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</span>
                      <span className="text-sm text-sky-400">{pct(strategy.winRate)} win rate</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <h2 className="mb-4 text-2xl font-extrabold text-white">Variance Context</h2>
              <p className="mb-8 text-sm text-slate-400">Strategies currently lagging</p>
              <div className="space-y-4">
                {strategyLaggards.map((strategy) => (
                  <div key={strategy.name} className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
                    <p className="font-semibold text-white">{strategy.name}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-2xl font-bold text-slate-400">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</span>
                      <span className="text-sm text-slate-400">{strategy.bets.toLocaleString()} bets</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Bankroll & Terms */}
        <section className="mb-32">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <h2 className="mb-4 text-2xl font-extrabold text-white">Bankroll Curve</h2>
              <p className="mb-8 text-sm text-slate-400">All-picks cumulative units</p>
              <Sparkline points={bankrollSeries} />
              <p className="mt-4 text-sm text-slate-400">+168 units from opening night through April 18 (even-money assumption)</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
              <h2 className="mb-8 text-2xl font-extrabold text-white">Term Guide</h2>
              <div className="space-y-4">
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
            </div>
          </div>
        </section>

        {/* Strategy Table */}
        <section className="mb-32">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8">
            <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <h2 className="text-2xl font-extrabold text-white">Strategy Board</h2>
                <p className="mt-1 text-sm text-slate-400">How each threshold performed in the 2023-24 season</p>
              </div>
              <p className="text-sm text-slate-500">Even-money assumption</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800">
                  <tr className="text-slate-400">
                    <th className="py-3 pr-4 text-left font-medium">Edge Gate</th>
                    <th className="py-3 px-4 text-left font-medium">Win %</th>
                    <th className="py-3 px-4 text-left font-medium">ROI / Bet</th>
                    <th className="py-3 px-4 text-left font-medium">Units</th>
                    <th className="py-3 px-4 text-left font-medium">Samples</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {strategies.map((strategy) => (
                    <tr key={strategy.name} className="text-slate-300">
                      <td className="py-3 pr-4 font-semibold text-white">{strategy.name}</td>
                      <td className="py-3 px-4">{pct(strategy.winRate)}</td>
                      <td className="py-3 px-4">{((strategy.units / strategy.bets) * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4 text-sky-400">{strategy.units > 0 ? `+${strategy.units}` : strategy.units}u</td>
                      <td className="py-3 px-4">{strategy.bets.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function Definition({ term, children }: { term: string; children: ReactNode }) {
  return (
    <article className="rounded-lg border border-slate-800/50 bg-slate-950/50 p-4">
      <p className="text-sm font-medium text-slate-400">{term}</p>
      <p className="mt-2 text-xs text-slate-300">{children}</p>
    </article>
  );
}

function Sparkline({ points }: { points: BankrollPoint[] }) {
  if (points.length === 0) {
    return <div className="text-sm text-slate-400">No bankroll history available.</div>;
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
        <path d={path} fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {points.slice(-4).map((point) => (
          <div key={point.label} className="rounded-lg border border-slate-800/50 bg-slate-950/50 px-3 py-2 text-center">
            <p className="text-slate-400">{point.label}</p>
            <p className="mt-1 font-semibold text-white">{point.units.toFixed(0)}u</p>
          </div>
        ))}
      </div>
    </div>
  );
}
