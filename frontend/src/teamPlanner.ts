import rawMapping from '../../utils/tft_set16_teamplanner_mapping.json';

export type TeamPlannerCodeResult = {
  code: string | null;
  missing: string[];
  trimmed: number;
};

export type TeamPlannerMapping = {
  set: string;
  format: string;
  order: string[];
  by_character_id: Record<string, string>;
  by_display_name: Record<string, string>;
};

const TEAM_PLANNER_PREFIX = '02';
const TEAM_PLANNER_SLOTS = 10;

const mapping = rawMapping as TeamPlannerMapping;
const suffix = mapping.set ?? 'TFTSet16';

const orderIndex = new Map<string, number>();
mapping.order.forEach((characterId, index) => {
  const hex = mapping.by_character_id[characterId];
  if (hex) {
    orderIndex.set(hex.toUpperCase(), index);
  }
});

const normalizeHex = (hex: string) => hex.toUpperCase().padStart(3, '0');

const lookupHexForUnit = (unit: string) =>
  mapping.by_display_name[unit] ?? mapping.by_character_id[unit];

export const buildTeamPlannerCode = (team: string[]): TeamPlannerCodeResult => {
  const seenHex = new Set<string>();
  const missing: string[] = [];
  const orderedHexes: { hex: string; position: number }[] = [];

  team.forEach((unit, position) => {
    const hex = lookupHexForUnit(unit);
    if (!hex) {
      missing.push(unit);
      return;
    }
    const normalized = normalizeHex(hex);
    if (seenHex.has(normalized)) return;
    seenHex.add(normalized);
    orderedHexes.push({ hex: normalized, position });
  });

  orderedHexes.sort((a, b) => {
    const orderA = orderIndex.get(a.hex) ?? Number.MAX_SAFE_INTEGER;
    const orderB = orderIndex.get(b.hex) ?? Number.MAX_SAFE_INTEGER;
    if (orderA !== orderB) return orderA - orderB;
    return a.position - b.position;
  });

  const trimmed = Math.max(0, orderedHexes.length - TEAM_PLANNER_SLOTS);
  const limitedHexes = orderedHexes.slice(0, TEAM_PLANNER_SLOTS).map((entry) => entry.hex);
  const paddedHexes = [
    ...limitedHexes,
    ...Array.from({ length: TEAM_PLANNER_SLOTS - limitedHexes.length }, () => '000'),
  ];

  const code = `${TEAM_PLANNER_PREFIX}${paddedHexes.join('')}${suffix}`;

  return { code, missing, trimmed };
};

export const getTeamPlannerSuffix = () => suffix;
export const getTeamPlannerSlotCount = () => TEAM_PLANNER_SLOTS;
