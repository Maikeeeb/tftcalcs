import { PaletteMode } from '@mui/material';

export type ConfigData = Record<string, unknown>;

export type AppProps = {
  mode: PaletteMode;
  onToggleColorMode: () => void;
};

export type SolverResponse = {
  context: Record<string, unknown> & { mode?: 'bronze' | 'standard' | 'ryze' | 'itemization' };
  debug_log?: string[];
  meta: {
    enabled: boolean;
    weights: {
      w_win: number;
      w_avg: number;
      w_freq: number;
    };
    unit_stats?: Record<string, { avg?: number; win?: number; freq?: number; items?: string[] }>;
    trait_stats_enabled?: boolean;
  };
  solution: {
    team: string[];
    emblems: Record<string, number>;
    team_power: number;
    bronze_count: number;
    trait_counts: Record<string, number>;
    bronze_traits: string[];
    active_traits: string[];
    upgraded_traits: string[];
    used_traits: string[];
    trait_metatft?: Record<
      string,
      { required: number; tier: string; avg?: number; win?: number; freq?: number }
    >;
  };
  units: Record<
    string,
    {
      traits: string[];
      cost?: number;
      metatft?: { avg?: number; win?: number; freq?: number; items?: string[] } | null;
    }
  >;
  requirements: {
    champions: Record<string, { rule: number; present: boolean; status: string; satisfied: boolean }>;
    traits: Record<string, { minimum: number; actual: number; satisfied: boolean }>;
    all_satisfied: boolean;
  };
};

export type ItemOption = {
  apiName: string;
  name: string;
  components?: string[];
  traits?: string[];
};

export type ItemizationReference = {
  components: ItemOption[];
  completed_items: ItemOption[];
  target_carries: ItemOption[];
  traits: string[];
};

export type ItemizationConfig = {
  available_components: string[];
  available_completed_items: string[];
  target_carries: string[];
  team_traits: string[];
  needed_traits: string[];
  allow_reforge: boolean;
};

export type ItemizationCandidate = {
  champion: string;
  cost?: number;
  traits: string[];
  ideal_items: string[];
  missing_components: string[];
  trait_shells: string[];
  team_trait_matches: string[];
  needed_trait_matches: string[];
  suggested_slams: string[];
  score: {
    full_items: number;
    completed_items: number;
    reforged_items: number;
    craftable_items: number;
    partial_components: number;
    matched_completed: string[];
    reforged: string[];
    craftable: string[];
    partial: { item: string; components_hit: number; missing_components: string[] }[];
    needed_trait_hits: number;
    team_trait_hits: number;
  };
};

export type ItemizationResult = {
  context: {
    mode: string;
    set_id: string;
    available_components: string[];
    available_completed_items: string[];
    team_traits: string[];
    needed_traits: string[];
    allow_reforge: boolean;
  };
  solution: {
    ranked_candidates: ItemizationCandidate[];
  };
  items: {
    components: string[];
    completed_items: string[];
    names_by_api: Record<string, string>;
  };
};

export type ItemizationRunResponse = {
  version: number;
  result: ItemizationResult;
};

export type MappingFieldOptions = {
  enumOptions?: { value: number; label: string }[];
  min?: number;
  heading?: string;
  searchPlaceholder?: string;
  imageType?: 'trait' | 'emblem' | 'champion';
  unlockableValues?: string[];
  championCosts?: Record<string, number>;
};
