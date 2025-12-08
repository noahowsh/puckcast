import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { fetchGoalieById, fetchGoalieStats } from "@/lib/playerHub";
import { getGoaliePulse } from "@/lib/data";
import { TeamLogo } from "@/components/TeamLogo";
import { TeamCrest } from "@/components/TeamCrest";
import type { GoalieCard } from "@/types/goalie";
import { parsePlayerSlug, generatePlayerSlug } from "@/lib/playerSlug";

export const revalidate = 3600; // Revalidate every hour

// Generate static params for the most active goalies (using slug format)
export async function generateStaticParams() {
  const allGoalies = await fetchGoalieStats(5);
  return allGoalies.slice(0, 50).map((g) => ({
    playerId: `${generatePlayerSlug(g.bio.fullName)}-${g.bio.playerId}`,
  }));
}

export default async function GoalieDetailPage({ params }: { params: Promise<{ playerId: string }> }) {
  const { playerId } = await params;
  const id = parsePlayerSlug(playerId);

  if (!id) {
    return notFound();
  }

  const goalie = await fetchGoalieById(id);
  if (!goalie) {
    return notFound();
  }

  const { bio, stats } = goalie;

  // Get goalie pulse data for this goalie if available
  const pulse = getGoaliePulse();
  const pulseData = pulse.goalies.find(
    (g) => g.name.toLowerCase().includes(bio.lastName.toLowerCase()) && g.team === bio.teamAbbrev
  );

  // Calculate league ranks
  const allGoalies = await fetchGoalieStats(3);
  const winsRank = [...allGoalies].sort((a, b) => b.stats.wins - a.stats.wins).findIndex((g) => g.bio.playerId === bio.playerId) + 1;
  const savePctRank = [...allGoalies].filter((g) => g.stats.gamesPlayed >= 10).sort((a, b) => b.stats.savePct - a.stats.savePct).findIndex((g) => g.bio.playerId === bio.playerId) + 1;
  const gaaRank = [...allGoalies].filter((g) => g.stats.gamesPlayed >= 10).sort((a, b) => a.stats.goalsAgainstAverage - b.stats.goalsAgainstAverage).findIndex((g) => g.bio.playerId === bio.playerId) + 1;

  // Calculate record string
  const record = `${stats.wins}-${stats.losses}-${stats.otLosses}`;

  // Per start averages
  const savePctDisplay = stats.savePct >= 1 ? stats.savePct.toFixed(3) : `.${Math.round(stats.savePct * 1000)}`;

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "6rem" }}>
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/goalies" className="text-sm text-white/50 hover:text-white/70 transition-colors">
            ← Back to Goalies
          </Link>
        </div>

        {/* Hero Section */}
        <section className="nova-hero mb-8">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <div className="flex items-center gap-3 mb-4">
                <TeamLogo teamAbbrev={bio.teamAbbrev} size="lg" />
                <div>
                  <h1 className="display-xl">{bio.fullName}</h1>
                  <p className="lead flex items-center gap-2">
                    <span>Goaltender</span>
                    <span className="text-white/30">•</span>
                    <span>{bio.teamAbbrev}</span>
                    {bio.jerseyNumber && (
                      <>
                        <span className="text-white/30">•</span>
                        <span>#{bio.jerseyNumber}</span>
                      </>
                    )}
                  </p>
                </div>
              </div>

              {/* Key Stats Grid */}
              <div className="grid grid-cols-4 gap-3 mt-6">
                <StatBox label="Record" value={record} />
                <StatBox label="SV%" value={savePctDisplay} rank={savePctRank > 0 ? savePctRank : undefined} color="sky" />
                <StatBox label="GAA" value={stats.goalsAgainstAverage.toFixed(2)} rank={gaaRank > 0 ? gaaRank : undefined} color="emerald" />
                <StatBox label="SO" value={stats.shutouts} color="amber" />
              </div>
            </div>

            {/* Goalie Card */}
            <div className="nova-hero__panel" style={{ padding: "1.5rem" }}>
              <div className="flex items-center gap-4 mb-6">
                {bio.headshot ? (
                  <Image
                    src={bio.headshot}
                    alt={bio.fullName}
                    width={100}
                    height={100}
                    className="rounded-full bg-white/[0.03]"
                  />
                ) : (
                  <div className="w-[100px] h-[100px] rounded-full bg-white/[0.06] flex items-center justify-center">
                    <TeamCrest abbrev={bio.teamAbbrev} size={64} />
                  </div>
                )}
                <div>
                  <p className="text-3xl font-bold text-emerald-400">{stats.wins}</p>
                  <p className="text-sm text-white/60">Wins</p>
                  <p className="text-xs text-white/40 mt-1">#{winsRank > 0 ? winsRank : "—"} NHL</p>
                </div>
              </div>

              {/* Bio Info */}
              <div className="space-y-2 text-sm">
                {bio.birthDate && (
                  <div className="flex justify-between">
                    <span className="text-white/50">Age</span>
                    <span className="text-white">{calculateAge(bio.birthDate)}</span>
                  </div>
                )}
                {bio.birthCity && bio.birthCountry && (
                  <div className="flex justify-between">
                    <span className="text-white/50">Born</span>
                    <span className="text-white">{bio.birthCity}, {bio.birthCountry}</span>
                  </div>
                )}
                {bio.heightInInches && (
                  <div className="flex justify-between">
                    <span className="text-white/50">Height</span>
                    <span className="text-white">{formatHeight(bio.heightInInches)}</span>
                  </div>
                )}
                {bio.weightInPounds && (
                  <div className="flex justify-between">
                    <span className="text-white/50">Weight</span>
                    <span className="text-white">{bio.weightInPounds} lbs</span>
                  </div>
                )}
                {bio.shootsCatches && (
                  <div className="flex justify-between">
                    <span className="text-white/50">Catches</span>
                    <span className="text-white">{bio.shootsCatches === "L" ? "Left" : "Right"}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Goalie Pulse Section */}
        {pulseData && (
          <section className="nova-section">
            <h2 className="text-xl font-bold text-white mb-4">Goalie Intelligence</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide">Form & Rest</h3>
                  <TrendBadge trend={pulseData.trend} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-white/[0.03] rounded-lg">
                    <p className={`text-2xl font-bold ${pulseData.rollingGsa > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {pulseData.rollingGsa > 0 ? "+" : ""}{pulseData.rollingGsa.toFixed(1)}
                    </p>
                    <p className="text-xs text-white/50 mt-1">Rolling GSAx</p>
                  </div>
                  <div className="text-center p-3 bg-white/[0.03] rounded-lg">
                    <p className="text-2xl font-bold text-white">{pulseData.restDays}d</p>
                    <p className="text-xs text-white/50 mt-1">Rest Days</p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-white/[0.06]">
                  <div className="flex justify-between text-sm">
                    <span className="text-white/50">Start Likelihood</span>
                    <span className="text-sky-300 font-semibold">{Math.round(pulseData.startLikelihood * 100)}%</span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-white/50">Season GSAx</span>
                    <span className={`font-semibold ${pulseData.seasonGsa > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {pulseData.seasonGsa > 0 ? "+" : ""}{pulseData.seasonGsa.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="card p-4">
                <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide mb-4">Analysis</h3>
                <p className="text-sm text-white/80 leading-relaxed mb-4">{pulseData.note}</p>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <p className="text-xs text-emerald-400 font-semibold mb-2 uppercase">Strengths</p>
                    <ul className="space-y-1">
                      {pulseData.strengths.slice(0, 2).map((s, i) => (
                        <li key={i} className="text-xs text-white/70 flex items-start gap-1">
                          <span className="text-emerald-400">✓</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs text-amber-400 font-semibold mb-2 uppercase">Watch</p>
                    <ul className="space-y-1">
                      {pulseData.watchouts.slice(0, 2).map((w, i) => (
                        <li key={i} className="text-xs text-white/70 flex items-start gap-1">
                          <span className="text-amber-400">!</span> {w}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {pulseData.nextOpponent && (
                  <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center justify-between">
                    <span className="text-sm text-white/50">Next Opponent</span>
                    <div className="flex items-center gap-2">
                      <TeamLogo teamAbbrev={pulseData.nextOpponent} size="xs" />
                      <span className="text-sm text-white font-medium">{pulseData.nextOpponent}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Season Stats */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">2024-25 Season Stats</h2>
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-white/50 uppercase tracking-wider border-b border-white/[0.06]">
                    <th className="py-3 px-4">GP</th>
                    <th className="py-3 px-4">GS</th>
                    <th className="py-3 px-4">W</th>
                    <th className="py-3 px-4">L</th>
                    <th className="py-3 px-4">OTL</th>
                    <th className="py-3 px-4">SA</th>
                    <th className="py-3 px-4">SV</th>
                    <th className="py-3 px-4">GA</th>
                    <th className="py-3 px-4">SV%</th>
                    <th className="py-3 px-4">GAA</th>
                    <th className="py-3 px-4">SO</th>
                    <th className="py-3 px-4">TOI</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-white/[0.04]">
                    <td className="py-3 px-4 text-white">{stats.gamesPlayed}</td>
                    <td className="py-3 px-4 text-white">{stats.gamesStarted}</td>
                    <td className="py-3 px-4 text-emerald-400 font-semibold">{stats.wins}</td>
                    <td className="py-3 px-4 text-white/70">{stats.losses}</td>
                    <td className="py-3 px-4 text-white/70">{stats.otLosses}</td>
                    <td className="py-3 px-4 text-white/70">{stats.shotsAgainst}</td>
                    <td className="py-3 px-4 text-white">{stats.saves}</td>
                    <td className="py-3 px-4 text-white/70">{stats.goalsAgainst}</td>
                    <td className="py-3 px-4 text-sky-300 font-bold">{savePctDisplay}</td>
                    <td className={`py-3 px-4 font-medium ${stats.goalsAgainstAverage < 2.5 ? "text-emerald-400" : stats.goalsAgainstAverage > 3.2 ? "text-rose-400" : "text-white"}`}>
                      {stats.goalsAgainstAverage.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-white">{stats.shutouts}</td>
                    <td className="py-3 px-4 text-white/70">{stats.timeOnIce}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Performance Metrics */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">Performance Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-sky-300">{savePctDisplay}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Save %</p>
              {savePctRank > 0 && <p className="text-xs text-white/30 mt-1">#{savePctRank} NHL</p>}
            </div>
            <div className="card p-4 text-center">
              <p className={`text-2xl font-bold ${stats.goalsAgainstAverage < 2.5 ? "text-emerald-400" : stats.goalsAgainstAverage > 3.0 ? "text-rose-400" : "text-white"}`}>
                {stats.goalsAgainstAverage.toFixed(2)}
              </p>
              <p className="text-xs text-white/50 uppercase mt-1">GAA</p>
              {gaaRank > 0 && <p className="text-xs text-white/30 mt-1">#{gaaRank} NHL</p>}
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-white">{stats.saves}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Total Saves</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-amber-400">{stats.shutouts}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Shutouts</p>
            </div>
          </div>
        </section>

        {/* Record Breakdown */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">Record Breakdown</h2>
          <div className="card p-4">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl font-bold text-white">{record}</span>
              <span className="text-white/40 text-sm">({stats.gamesPlayed} GP)</span>
            </div>

            {/* Record bar */}
            <div className="flex h-8 rounded-lg overflow-hidden mb-4">
              <div
                className="bg-emerald-500 flex items-center justify-center"
                style={{ width: `${(stats.wins / stats.gamesPlayed) * 100}%` }}
              >
                {stats.wins > 0 && <span className="text-sm font-bold text-white">{stats.wins}W</span>}
              </div>
              <div
                className="bg-rose-500 flex items-center justify-center"
                style={{ width: `${(stats.losses / stats.gamesPlayed) * 100}%` }}
              >
                {stats.losses > 0 && <span className="text-sm font-bold text-white">{stats.losses}L</span>}
              </div>
              {stats.otLosses > 0 && (
                <div
                  className="bg-amber-500 flex items-center justify-center"
                  style={{ width: `${(stats.otLosses / stats.gamesPlayed) * 100}%` }}
                >
                  <span className="text-sm font-bold text-white">{stats.otLosses}OT</span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-xl font-bold text-emerald-400">{((stats.wins / stats.gamesPlayed) * 100).toFixed(0)}%</p>
                <p className="text-xs text-white/50">Win Rate</p>
              </div>
              <div>
                <p className="text-xl font-bold text-white">{(stats.gamesStarted / stats.gamesPlayed * 100).toFixed(0)}%</p>
                <p className="text-xs text-white/50">Start Rate</p>
              </div>
              <div>
                <p className="text-xl font-bold text-white">{stats.shotsAgainst > 0 ? (stats.saves / stats.gamesPlayed).toFixed(1) : "—"}</p>
                <p className="text-xs text-white/50">Saves/Game</p>
              </div>
            </div>
          </div>
        </section>

        {/* Link to Team */}
        <section className="nova-section">
          <Link href={`/teams/${bio.teamAbbrev.toLowerCase()}`} className="card p-4 flex items-center justify-between hover:border-white/20 transition-colors">
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbrev={bio.teamAbbrev} size="md" />
              <div>
                <p className="font-semibold text-white">View Team Stats</p>
                <p className="text-sm text-white/50">{bio.teamAbbrev} roster and team performance</p>
              </div>
            </div>
            <svg className="w-5 h-5 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </section>
      </div>
    </div>
  );
}

// =============================================================================
// Helper Components
// =============================================================================

function StatBox({
  label,
  value,
  rank,
  color,
}: {
  label: string;
  value: string | number;
  rank?: number;
  color?: "sky" | "emerald" | "amber";
}) {
  const colorClasses = {
    sky: "text-sky-300",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
  };

  const valueColor = color ? colorClasses[color] : "text-white";

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg text-center">
      <p className={`text-xl font-bold ${valueColor}`}>{value}</p>
      <p className="text-[10px] text-white/50 uppercase mt-1">{label}</p>
      {rank && rank > 0 && (
        <p className="text-xs text-white/40 mt-1">#{rank} NHL</p>
      )}
    </div>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  const trendConfig: Record<string, { color: string; icon: string }> = {
    surging: { color: "text-emerald-300 bg-emerald-500/20", icon: "↑" },
    steady: { color: "text-sky-300 bg-sky-500/20", icon: "→" },
    fresh: { color: "text-cyan-300 bg-cyan-500/20", icon: "★" },
    "fatigue watch": { color: "text-amber-300 bg-amber-500/20", icon: "!" },
  };

  const config = trendConfig[trend] || { color: "text-white/60 bg-white/10", icon: "•" };

  return (
    <span className={`text-xs font-semibold px-2 py-1 rounded ${config.color}`}>
      {config.icon} {trend}
    </span>
  );
}

// =============================================================================
// Helper Functions
// =============================================================================

function calculateAge(birthDate: string): number {
  const birth = new Date(birthDate);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }
  return age;
}

function formatHeight(inches: number): string {
  const feet = Math.floor(inches / 12);
  const remainingInches = inches % 12;
  return `${feet}'${remainingInches}"`;
}
