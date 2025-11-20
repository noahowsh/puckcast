// Stub for player hub context
// TODO: Implement full player hub integration

export interface PlayerHubContext {
  specialTeams?: {
    teams: Record<string, any>;
  } | null;
  goalieShotProfiles?: any[];
}

export function getPlayerHubContext(): PlayerHubContext {
  return {
    specialTeams: null,
    goalieShotProfiles: [],
  };
}
