import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { fetchSkaterById, fetchSkaterStats } from "@/lib/playerHub";
import { TeamLogo } from "@/components/TeamLogo";
import { TeamCrest } from "@/components/TeamCrest";
import { SeasonProjectionCard } from "@/components/SeasonProjectionCard";
import { SkillProfileCard } from "@/components/SkillProfileCard";
import { OnIceImpactCard } from "@/components/OnIceImpactCard";
import {
  generateSeasonProjection,
  generateSkillProfile,
  generateOnIceImpact,
} from "@/lib/playerProjections";
import { parsePlayerSlug, generatePlayerSlug } from "@/lib/playerSlug";

export const revalidate = 3600; // Revalidate every hour

// Generate static params for the most active players (using slug format)
export async function generateStaticParams() {
  const allSkaters = await fetchSkaterStats(10);
  return allSkaters.slice(0, 100).map((p) => ({
    playerId: `${generatePlayerSlug(p.bio.fullName)}-${p.bio.playerId}`,
  }));
}

export default async function PlayerDetailPage({ params }: { params: Promise<{ playerId: string }> }) {
  const { playerId } = await params;
  const id = parsePlayerSlug(playerId);

  if (!id) {
    return notFound();
  }

  const player = await fetchSkaterById(id);
  if (!player) {
    return notFound();
  }

  const { bio, stats } = player;

  // Calculate league ranks
  const allSkaters = await fetchSkaterStats(5);
  const pointsRank = allSkaters.findIndex((p) => p.bio.playerId === bio.playerId) + 1;
  const goalsRank = [...allSkaters].sort((a, b) => b.stats.goals - a.stats.goals).findIndex((p) => p.bio.playerId === bio.playerId) + 1;
  const assistsRank = [...allSkaters].sort((a, b) => b.stats.assists - a.stats.assists).findIndex((p) => p.bio.playerId === bio.playerId) + 1;

  // Generate advanced analytics data
  const seasonProjection = generateSeasonProjection(player, allSkaters);
  const skillProfile = generateSkillProfile(player, allSkaters);
  const onIceImpact = generateOnIceImpact(player, allSkaters);

  // Calculate player age
  const playerAge = bio.birthDate ? calculateAge(bio.birthDate) : undefined;

  const positionLabels: Record<string, string> = {
    C: "Center",
    L: "Left Wing",
    R: "Right Wing",
    D: "Defenseman",
  };

  const positionLabel = positionLabels[bio.position] || bio.position;

  // Calculate per-game stats
  const pointsPerGame = stats.gamesPlayed > 0 ? (stats.points / stats.gamesPlayed).toFixed(2) : "0.00";
  const goalsPerGame = stats.gamesPlayed > 0 ? (stats.goals / stats.gamesPlayed).toFixed(2) : "0.00";
  const shotsPerGame = stats.gamesPlayed > 0 ? (stats.shots / stats.gamesPlayed).toFixed(1) : "0.0";

  return (
    <div className="min-h-screen">
      <div className="container" style={{ paddingTop: "5rem" }}>
        {/* Breadcrumb */}
        <div className="mb-4">
          <Link href="/players" className="text-sm text-white/50 hover:text-white/70 transition-colors">
            ← Back to Players
          </Link>
        </div>

        {/* Hero Section */}
        <section className="nova-hero mb-8">
          <div className="nova-hero__grid nova-hero__grid--balanced">
            <div className="nova-hero__text">
              <div className="flex items-center gap-4 mb-4">
                {bio.headshot ? (
                  <Image
                    src={bio.headshot}
                    alt={bio.fullName}
                    width={80}
                    height={80}
                    className="rounded-full bg-white/[0.03] flex-shrink-0"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0">
                    <TeamCrest abbrev={bio.teamAbbrev} size={48} />
                  </div>
                )}
                <div>
                  <h1 className="display-lg">{bio.fullName}</h1>
                  <div className="flex items-center gap-2 mt-1">
                    <TeamLogo teamAbbrev={bio.teamAbbrev} size="sm" />
                    <span className="text-white/60">{positionLabel}</span>
                    {bio.jerseyNumber && (
                      <>
                        <span className="text-white/30">•</span>
                        <span className="text-white/60">#{bio.jerseyNumber}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Bio details */}
              <div className="flex items-center gap-4 text-sm text-white/50 mb-6">
                {playerAge && <span>{playerAge} years old</span>}
                {bio.heightInInches && <span>{formatHeight(bio.heightInInches)}</span>}
                {bio.weightInPounds && <span>{bio.weightInPounds} lbs</span>}
                {bio.birthCity && bio.birthCountry && (
                  <span>{bio.birthCity}, {bio.birthCountry}</span>
                )}
              </div>

              {/* Key Stats Grid */}
              <div className="grid grid-cols-4 gap-4">
                <KeyStat label="Points" value={stats.points} rank={pointsRank > 0 ? pointsRank : undefined} color="sky" />
                <KeyStat label="Goals" value={stats.goals} rank={goalsRank > 0 ? goalsRank : undefined} color="emerald" />
                <KeyStat label="Assists" value={stats.assists} rank={assistsRank > 0 ? assistsRank : undefined} color="amber" />
                <KeyStat label="+/-" value={stats.plusMinus} plusMinus />
              </div>
            </div>

            {/* Right Panel - Per Game Stats */}
            <div className="nova-hero__panel" style={{ padding: "1.5rem" }}>
              <p className="text-xs font-semibold text-white/50 uppercase tracking-wide mb-4">Per Game Averages</p>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="text-center p-3 bg-white/[0.03] rounded-lg">
                  <p className="text-2xl font-bold text-sky-300">{pointsPerGame}</p>
                  <p className="text-xs text-white/50">Points/Game</p>
                </div>
                <div className="text-center p-3 bg-white/[0.03] rounded-lg">
                  <p className="text-2xl font-bold text-emerald-400">{goalsPerGame}</p>
                  <p className="text-xs text-white/50">Goals/Game</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/50">Shots/Game</span>
                  <span className="text-sm font-semibold text-white">{shotsPerGame}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/50">TOI/Game</span>
                  <span className="text-sm font-semibold text-white">{stats.timeOnIcePerGame}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-white/50">Games Played</span>
                  <span className="text-sm font-semibold text-white">{stats.gamesPlayed}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Season Stats Table */}
        <section className="nova-section">
          <h2 className="text-lg font-bold text-white mb-4">2024-25 Season Stats</h2>
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[10px] text-white/50 uppercase tracking-wider border-b border-white/[0.06]">
                    <th className="py-2.5 px-3">GP</th>
                    <th className="py-2.5 px-3">G</th>
                    <th className="py-2.5 px-3">A</th>
                    <th className="py-2.5 px-3">P</th>
                    <th className="py-2.5 px-3">+/-</th>
                    <th className="py-2.5 px-3">PIM</th>
                    <th className="py-2.5 px-3">PPG</th>
                    <th className="py-2.5 px-3">PPP</th>
                    <th className="py-2.5 px-3">SHG</th>
                    <th className="py-2.5 px-3">GWG</th>
                    <th className="py-2.5 px-3">S</th>
                    <th className="py-2.5 px-3">S%</th>
                    <th className="py-2.5 px-3">TOI/G</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="py-2.5 px-3 text-white">{stats.gamesPlayed}</td>
                    <td className="py-2.5 px-3 text-white font-semibold">{stats.goals}</td>
                    <td className="py-2.5 px-3 text-white font-semibold">{stats.assists}</td>
                    <td className="py-2.5 px-3 text-sky-300 font-bold">{stats.points}</td>
                    <td className={`py-2.5 px-3 font-medium ${stats.plusMinus > 0 ? "text-emerald-400" : stats.plusMinus < 0 ? "text-rose-400" : "text-white/60"}`}>
                      {stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}
                    </td>
                    <td className="py-2.5 px-3 text-white/60">{stats.penaltyMinutes}</td>
                    <td className="py-2.5 px-3 text-white/60">{stats.powerPlayGoals}</td>
                    <td className="py-2.5 px-3 text-white/60">{stats.powerPlayPoints}</td>
                    <td className="py-2.5 px-3 text-white/60">{stats.shorthandedGoals}</td>
                    <td className="py-2.5 px-3 text-white/60">{stats.gameWinningGoals}</td>
                    <td className="py-2.5 px-3 text-white/60">{stats.shots}</td>
                    <td className="py-2.5 px-3 text-white/60">
                      {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-white/60">{stats.timeOnIcePerGame}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Scoring Breakdown */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <h2 className="text-lg font-bold text-white mb-4">Scoring Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card p-4">
              <h3 className="text-xs font-semibold text-white/60 mb-3 uppercase tracking-wide">Goals by Situation</h3>
              <div className="space-y-2">
                <ProgressBar label="Even Strength" value={stats.goals - stats.powerPlayGoals - stats.shorthandedGoals} total={stats.goals} />
                <ProgressBar label="Power Play" value={stats.powerPlayGoals} total={stats.goals} color="amber" />
                <ProgressBar label="Shorthanded" value={stats.shorthandedGoals} total={stats.goals} color="rose" />
              </div>
            </div>
            <div className="card p-4">
              <h3 className="text-xs font-semibold text-white/60 mb-3 uppercase tracking-wide">Points Distribution</h3>
              <div className="space-y-2">
                <ProgressBar label="Goals" value={stats.goals} total={stats.points} color="emerald" />
                <ProgressBar label="Assists" value={stats.assists} total={stats.points} color="sky" />
              </div>
              <div className="mt-3 pt-3 border-t border-white/[0.06] flex gap-4 text-xs">
                <div>
                  <span className="text-white/50">GWG: </span>
                  <span className="text-white font-medium">{stats.gameWinningGoals}</span>
                </div>
                <div>
                  <span className="text-white/50">OT: </span>
                  <span className="text-white font-medium">{stats.overtimeGoals}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Advanced Analytics Section */}
        <section className="nova-section" style={{ paddingTop: 0 }}>
          <div className="section-head mb-6">
            <div>
              <div className="flex items-center gap-2">
                <p className="eyebrow">Player Intelligence</p>
                <span className="text-[10px] text-white/40 bg-white/[0.06] px-2 py-0.5 rounded-full">Beta</span>
              </div>
              <h2>Advanced Analytics</h2>
              <p className="lead-sm">Projections, skill profile, and on-ice impact metrics.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SeasonProjectionCard projection={seasonProjection} playerName={bio.fullName} />
            <SkillProfileCard profile={skillProfile} playerName={bio.fullName} age={playerAge} evTOI={stats.timeOnIcePerGame} />
          </div>

          <div className="mt-6">
            <OnIceImpactCard impact={onIceImpact} playerName={bio.fullName} age={playerAge} />
          </div>
        </section>

        {/* Link to Team */}
        <section className="mb-8">
          <Link href={`/teams/${bio.teamAbbrev.toLowerCase()}`} className="card p-4 flex items-center justify-between hover:border-white/20 transition-colors">
            <div className="flex items-center gap-3">
              <TeamLogo teamAbbrev={bio.teamAbbrev} size="md" />
              <div>
                <p className="font-semibold text-white text-sm">View Team Stats</p>
                <p className="text-xs text-white/50">{bio.teamAbbrev} roster and performance</p>
              </div>
            </div>
            <svg className="w-4 h-4 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

function KeyStat({
  label,
  value,
  rank,
  color,
  plusMinus,
}: {
  label: string;
  value: number;
  rank?: number;
  color?: "sky" | "emerald" | "amber";
  plusMinus?: boolean;
}) {
  const colorClasses = {
    sky: "text-sky-300",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
  };

  const valueColor = plusMinus
    ? value > 0 ? "text-emerald-400" : value < 0 ? "text-rose-400" : "text-white"
    : color ? colorClasses[color] : "text-white";

  const displayValue = plusMinus && value > 0 ? `+${value}` : value;

  return (
    <div className="text-center">
      <p className={`text-2xl lg:text-3xl font-bold ${valueColor}`}>{displayValue}</p>
      <p className="text-[10px] text-white/50 uppercase mt-0.5">{label}</p>
      {rank && rank > 0 && rank <= 20 && (
        <p className="text-[10px] text-white/30 mt-0.5">#{rank} NHL</p>
      )}
    </div>
  );
}

function ProgressBar({
  label,
  value,
  total,
  color = "sky",
}: {
  label: string;
  value: number;
  total: number;
  color?: "sky" | "emerald" | "amber" | "rose";
}) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  const colorClasses = {
    sky: "bg-sky-400",
    emerald: "bg-emerald-400",
    amber: "bg-amber-400",
    rose: "bg-rose-400",
  };

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-white/60">{label}</span>
        <span className="text-white font-medium">{value}</span>
      </div>
      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div className={`h-full ${colorClasses[color]} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
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
