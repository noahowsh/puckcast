"use client";

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import insightsData from "@/data/modelInsights.json";
import type { ModelInsights } from "@/types/insights";

const modelInsights = insightsData as ModelInsights;
const strategies = modelInsights.strategies;
const bankrollSeries = modelInsights.bankrollSeries;
const sortedStrategies = [...strategies].sort((a, b) => b.units - a.units);

const edgeOptions = [0, 5, 10, 15, 20];

function edgeFromName(name: string) {
  const match = name.match(/(\d+)\s*pts/);
  return match ? parseInt(match[1], 10) : 0;
}

const strategyByEdge = strategies.reduce<Record<number, typeof strategies[0]>>((acc, strategy) => {
  acc[edgeFromName(strategy.name)] = strategy;
  return acc;
}, {});

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function BettingPage() {
  const [edgeThreshold, setEdgeThreshold] = useState(10);

  const activeStrategy = useMemo(() => {
    const closest = edgeOptions.reduce((prev, curr) =>
      Math.abs(curr - edgeThreshold) < Math.abs(prev - edgeThreshold) ? curr : prev
    );
    return strategyByEdge[closest] ?? strategies[0];
  }, [edgeThreshold]);

  const roiPerBet = ((activeStrategy.units / activeStrategy.bets) * 100).toFixed(1);

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "8rem" }}>
        <PageHeader
          title="Betting Lab"
          description="Interactive strategy sandbox. Adjust edge thresholds to see historical win rate, ROI, and bankroll curves from our 4,722 game test set."
          icon={
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          }
        />

        {/* Interactive Edge Slider */}
        <section className="mb-12 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="card-elevated">
            <h2 className="text-2xl font-bold text-white mb-3">Edge threshold explorer</h2>
            <p className="text-white/70 mb-6">Slide to see how different edge thresholds perform historically.</p>

            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-semibold text-white/80">Minimum edge threshold</label>
                <span className="text-3xl font-bold text-gradient">{edgeThreshold} pts</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="1"
                value={edgeThreshold}
                onChange={(e) => setEdgeThreshold(Number(e.target.value))}
                className="w-full h-3 rounded-full appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, rgb(34, 211, 238) 0%, rgb(34, 211, 238) ${(edgeThreshold / 20) * 100}%, rgb(51, 65, 85) ${(edgeThreshold / 20) * 100}%, rgb(51, 65, 85) 100%)`,
                }}
              />
              <div className="flex justify-between text-xs text-white/60 mt-2">
                <span>0 pts (all games)</span>
                <span>20+ pts (high confidence only)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Win rate"
                value={pct(activeStrategy.winRate)}
                change={{ value: `vs ${pct(0.5)} coin flip`, isPositive: activeStrategy.winRate > 0.5 }}
              />
              <StatCard label="Total bets" value={activeStrategy.bets.toLocaleString()} />
              <StatCard
                label="ROI per bet"
                value={`${roiPerBet}%`}
                change={{ value: roiPerBet, isPositive: parseFloat(roiPerBet) > 0 }}
              />
              <StatCard
                label="Total units"
                value={`${activeStrategy.units > 0 ? "+" : ""}${activeStrategy.units.toFixed(0)}u`}
                change={{ value: "Even money", isPositive: activeStrategy.units > 0 }}
                size="lg"
              />
            </div>
          </div>

          <div className="card">
            <h3 className="text-xl font-bold text-white mb-2">Bankroll curve</h3>
            <p className="text-sm text-white/70 mb-4">Flat stakes across historical bets</p>
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
              <BankrollChart points={bankrollSeries} />
            </div>
            <p className="mt-3 text-sm text-white/70">Final balance: +{(bankrollSeries.at(-1)?.units ?? 0).toFixed(0)}u</p>
          </div>
        </section>

        {/* Strategy Comparison */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-4">Strategy comparison</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Win Rate</th>
                  <th>Total Bets</th>
                  <th>ROI/Bet</th>
                  <th>Units</th>
                  <th>Avg Edge</th>
                </tr>
              </thead>
              <tbody>
                {sortedStrategies.map((strategy) => {
                  const stratRoi = ((strategy.units / strategy.bets) * 100).toFixed(1);
                  const isProfitable = strategy.units > 0;

                  return (
                    <tr key={strategy.name}>
                      <td>
                        <div>
                          <div className="font-semibold text-white">{strategy.name}</div>
                          <div className="text-xs text-white/60">{strategy.note}</div>
                        </div>
                      </td>
                      <td className="font-semibold">{pct(strategy.winRate)}</td>
                      <td>{strategy.bets.toLocaleString()}</td>
                      <td className={isProfitable ? "text-emerald-300" : "text-rose-300"}>{stratRoi}%</td>
                      <td>
                        <span className={`font-bold ${isProfitable ? "text-emerald-300" : "text-rose-300"}`}>
                          {isProfitable ? "+" : ""}
                          {strategy.units.toFixed(0)}u
                        </span>
                      </td>
                      <td className="text-sky-200">{(strategy.avgEdge * 100).toFixed(1)} pts</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* Educational Content */}
        <section className="mb-12 grid gap-6 md:grid-cols-2">
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Kelly Criterion</h3>
            <p className="text-sm text-white/80 leading-relaxed mb-3">
              The Kelly Criterion suggests bet sizing proportional to your edge. Formula: f_star = (bp - q) / b; p = win probability, q = 1 - p,
              and b = odds (even money = 1).
            </p>
            <div className="text-xs text-white/60">Example: 60% win rate -&gt; Kelly suggests ~20% of bankroll.</div>
          </div>

          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">Bankroll management</h3>
            <p className="text-sm text-white/80 leading-relaxed mb-3">
              Never bet more than you can afford to lose. Most experts recommend 1-5% of your bankroll per bet, even with an edge.
            </p>
            <div className="text-xs text-white/60">Conservative: 1-2% | Moderate: 2-3% | Aggressive: 3-5%</div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="mb-12">
          <div className="card-elevated bg-amber-500/5 border-amber-500/30">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-amber-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <h3 className="text-lg font-bold text-amber-400 mb-2">Important disclaimer</h3>
                <p className="text-sm text-white/80 leading-relaxed">
                  Puckcast is an analytics and educational platform, not a betting service. We do not recommend specific wagers or guarantee profits.
                  Past performance does not predict future results. Sports betting involves risk - please gamble responsibly and only with money you can
                  afford to lose.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

type BankrollPoint = ModelInsights["bankrollSeries"][number];

function BankrollChart({ points }: { points: BankrollPoint[] }) {
  if (!points.length) return <p className="text-sm text-white/60">No bankroll history available.</p>;

  const max = Math.max(...points.map((p) => p.units));
  const min = Math.min(...points.map((p) => p.units));
  const range = max - min;
  const span = Math.max(points.length - 1, 1);

  const normalized = points.map((point, idx) => ({ x: (idx / span) * 100, y: range === 0 ? 50 : ((point.units - min) / range) * 80 + 10 }));
  const path = normalized.map((point, idx) => `${idx === 0 ? "M" : "L"} ${point.x} ${100 - point.y}`).join(" ");
  const areaPath = `${path} L 100 100 L 0 100 Z`;

  return (
    <svg viewBox="0 0 100 100" className="w-full h-36" preserveAspectRatio="none">
      <defs>
        <linearGradient id="bankrollGradientBet" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="rgb(34, 211, 238)" stopOpacity="0.25" />
          <stop offset="100%" stopColor="rgb(34, 211, 238)" stopOpacity="0.05" />
        </linearGradient>
        <linearGradient id="bankrollLineBet" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="rgb(34, 211, 238)" />
          <stop offset="100%" stopColor="rgb(52, 211, 153)" />
        </linearGradient>
      </defs>

      <path d={areaPath} fill="url(#bankrollGradientBet)" />
      <path d={path} fill="none" stroke="url(#bankrollLineBet)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
