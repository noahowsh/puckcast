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

export const revalidate = 3600; // Revalidate every hour

// Generate static params for the most active players
export async function generateStaticParams() {
  const allSkaters = await fetchSkaterStats(10);
  return allSkaters.slice(0, 100).map((p) => ({
    playerId: String(p.bio.playerId),
  }));
}

export default async function PlayerDetailPage({ params }: { params: Promise<{ playerId: string }> }) {
  const { playerId } = await params;
  const id = parseInt(playerId, 10);

  if (isNaN(id)) {
    return notFound();
  }

  const player = await fetchSkaterById(id);
  if (!player) {
    return notFound();
  }

  const { bio, stats } = player;

  // Calculate league ranks (simplified - would need full data for accurate ranks)
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
      <div className="container" style={{ paddingTop: "6rem" }}>
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/players" className="text-sm text-white/50 hover:text-white/70 transition-colors">
            ← Back to Players
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
                    <span>{positionLabel}</span>
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
                <StatBox label="Points" value={stats.points} rank={pointsRank > 0 ? pointsRank : undefined} color="sky" />
                <StatBox label="Goals" value={stats.goals} rank={goalsRank > 0 ? goalsRank : undefined} color="emerald" />
                <StatBox label="Assists" value={stats.assists} rank={assistsRank > 0 ? assistsRank : undefined} color="amber" />
                <StatBox label="+/-" value={stats.plusMinus} colored />
              </div>
            </div>

            {/* Player Card */}
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
                  <p className="text-3xl font-bold text-white">{stats.points}</p>
                  <p className="text-sm text-white/60">Total Points</p>
                  <p className="text-xs text-sky-300 mt-1">{pointsPerGame} P/G</p>
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
                    <span className="text-white/50">Shoots</span>
                    <span className="text-white">{bio.shootsCatches === "L" ? "Left" : "Right"}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Season Stats */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">2024-25 Season Stats</h2>
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-white/50 uppercase tracking-wider border-b border-white/[0.06]">
                    <th className="py-3 px-4">GP</th>
                    <th className="py-3 px-4">G</th>
                    <th className="py-3 px-4">A</th>
                    <th className="py-3 px-4">P</th>
                    <th className="py-3 px-4">+/-</th>
                    <th className="py-3 px-4">PIM</th>
                    <th className="py-3 px-4">PPG</th>
                    <th className="py-3 px-4">PPP</th>
                    <th className="py-3 px-4">SHG</th>
                    <th className="py-3 px-4">GWG</th>
                    <th className="py-3 px-4">S</th>
                    <th className="py-3 px-4">S%</th>
                    <th className="py-3 px-4">TOI/G</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-white/[0.04]">
                    <td className="py-3 px-4 text-white">{stats.gamesPlayed}</td>
                    <td className="py-3 px-4 text-white font-semibold">{stats.goals}</td>
                    <td className="py-3 px-4 text-white font-semibold">{stats.assists}</td>
                    <td className="py-3 px-4 text-sky-300 font-bold">{stats.points}</td>
                    <td className={`py-3 px-4 font-medium ${stats.plusMinus > 0 ? "text-emerald-400" : stats.plusMinus < 0 ? "text-rose-400" : "text-white/60"}`}>
                      {stats.plusMinus > 0 ? `+${stats.plusMinus}` : stats.plusMinus}
                    </td>
                    <td className="py-3 px-4 text-white/70">{stats.penaltyMinutes}</td>
                    <td className="py-3 px-4 text-white/70">{stats.powerPlayGoals}</td>
                    <td className="py-3 px-4 text-white/70">{stats.powerPlayPoints}</td>
                    <td className="py-3 px-4 text-white/70">{stats.shorthandedGoals}</td>
                    <td className="py-3 px-4 text-white/70">{stats.gameWinningGoals}</td>
                    <td className="py-3 px-4 text-white/70">{stats.shots}</td>
                    <td className="py-3 px-4 text-white/70">
                      {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                    </td>
                    <td className="py-3 px-4 text-white/70">{stats.timeOnIcePerGame}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Per Game Stats */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">Per Game Averages</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-sky-300">{pointsPerGame}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Points/Game</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-emerald-400">{goalsPerGame}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Goals/Game</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-white">{shotsPerGame}</p>
              <p className="text-xs text-white/50 uppercase mt-1">Shots/Game</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-white">{stats.timeOnIcePerGame}</p>
              <p className="text-xs text-white/50 uppercase mt-1">TOI/Game</p>
            </div>
          </div>
        </section>

        {/* Scoring Breakdown */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">Scoring Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Goals Breakdown */}
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wide">Goals by Situation</h3>
              <div className="space-y-3">
                <ProgressBar label="Even Strength" value={stats.goals - stats.powerPlayGoals - stats.shorthandedGoals} total={stats.goals} />
                <ProgressBar label="Power Play" value={stats.powerPlayGoals} total={stats.goals} color="amber" />
                <ProgressBar label="Shorthanded" value={stats.shorthandedGoals} total={stats.goals} color="rose" />
              </div>
            </div>

            {/* Points Breakdown */}
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wide">Points Distribution</h3>
              <div className="space-y-3">
                <ProgressBar label="Goals" value={stats.goals} total={stats.points} color="emerald" />
                <ProgressBar label="Assists" value={stats.assists} total={stats.points} color="sky" />
              </div>
              <div className="mt-4 pt-4 border-t border-white/[0.06]">
                <div className="flex justify-between text-sm">
                  <span className="text-white/50">Game Winners</span>
                  <span className="text-white font-semibold">{stats.gameWinningGoals}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-white/50">Overtime Goals</span>
                  <span className="text-white font-semibold">{stats.overtimeGoals}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Shooting Stats */}
        <section className="nova-section">
          <h2 className="text-xl font-bold text-white mb-4">Shooting</h2>
          <div className="card p-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-3xl font-bold text-white">{stats.shots}</p>
                <p className="text-xs text-white/50 uppercase mt-1">Total Shots</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-emerald-400">
                  {stats.shootingPct > 0 ? `${(stats.shootingPct * 100).toFixed(1)}%` : "—"}
                </p>
                <p className="text-xs text-white/50 uppercase mt-1">Shooting %</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-white">{shotsPerGame}</p>
                <p className="text-xs text-white/50 uppercase mt-1">Shots/Game</p>
              </div>
            </div>
          </div>
        </section>

        {/* Advanced Analytics Section */}
        <section className="nova-section">
          <div className="flex items-center gap-3 mb-6">
            <h2 className="text-xl font-bold text-white">Advanced Analytics</h2>
            <span className="text-xs text-white/40 bg-white/[0.05] px-2 py-1 rounded">Beta</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Season Projection Card */}
            <SeasonProjectionCard
              projection={seasonProjection}
              playerName={bio.fullName}
            />

            {/* Skill Profile Card */}
            <SkillProfileCard
              profile={skillProfile}
              playerName={bio.fullName}
              age={playerAge}
              evTOI={stats.timeOnIcePerGame}
            />
          </div>

          {/* On-Ice Impact Card - Full Width */}
          <div className="mt-6">
            <OnIceImpactCard
              impact={onIceImpact}
              playerName={bio.fullName}
              age={playerAge}
            />
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
  colored,
}: {
  label: string;
  value: number;
  rank?: number;
  color?: "sky" | "emerald" | "amber";
  colored?: boolean;
}) {
  const colorClasses = {
    sky: "text-sky-300",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
  };

  const valueColor = colored
    ? value > 0
      ? "text-emerald-400"
      : value < 0
        ? "text-rose-400"
        : "text-white"
    : color
      ? colorClasses[color]
      : "text-white";

  const displayValue = colored && value > 0 ? `+${value}` : value;

  return (
    <div className="p-3 bg-white/[0.03] rounded-lg text-center">
      <p className={`text-2xl font-bold ${valueColor}`}>{displayValue}</p>
      <p className="text-[10px] text-white/50 uppercase mt-1">{label}</p>
      {rank && rank > 0 && (
        <p className="text-xs text-white/40 mt-1">#{rank} NHL</p>
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
      <div className="flex justify-between text-sm mb-1">
        <span className="text-white/70">{label}</span>
        <span className="text-white font-medium">{value}</span>
      </div>
      <div className="h-2 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
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
