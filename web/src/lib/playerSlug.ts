// Player Slug Utilities
// Generates and parses URL-friendly slugs from player names

/**
 * Generate a URL-friendly slug from a player name
 * "Connor McDavid" -> "connor-mcdavid"
 * "Nikita Kucherov" -> "nikita-kucherov"
 * "Alexis Lafrenière" -> "alexis-lafreniere"
 */
export function generatePlayerSlug(fullName: string): string {
  return fullName
    .toLowerCase()
    // Normalize unicode characters (é -> e, etc.)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    // Replace spaces and special chars with hyphens
    .replace(/[^a-z0-9]+/g, "-")
    // Remove leading/trailing hyphens
    .replace(/^-+|-+$/g, "");
}

/**
 * Check if a string looks like a player ID (numeric)
 */
export function isNumericId(value: string): boolean {
  return /^\d+$/.test(value);
}

/**
 * Get player URL with slug
 * Returns the full path like "/players/connor-mcdavid-8478402"
 */
export function getPlayerUrl(playerId: number, fullName: string): string {
  const slug = generatePlayerSlug(fullName);
  return `/players/${slug}-${playerId}`;
}

/**
 * Get goalie URL with slug
 * Returns the full path like "/goalies/connor-hellebuyck-8476945"
 */
export function getGoalieUrl(playerId: number, fullName: string): string {
  const slug = generatePlayerSlug(fullName);
  return `/goalies/${slug}-${playerId}`;
}

/**
 * Parse a player slug to extract the ID
 * "connor-mcdavid-8478402" -> 8478402
 * "8478402" -> 8478402 (backwards compatible with numeric-only IDs)
 */
export function parsePlayerSlug(slug: string): number | null {
  // If it's just a number, return it directly (backwards compatibility)
  if (isNumericId(slug)) {
    return parseInt(slug, 10);
  }

  // Extract the ID from the end of the slug (format: name-slug-id)
  const match = slug.match(/-(\d+)$/);
  if (match) {
    return parseInt(match[1], 10);
  }

  return null;
}
