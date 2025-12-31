import { PaletteMode } from '@mui/material';

export type ConfigData = Record<string, unknown>;

export type AppProps = {
  mode: PaletteMode;
  onToggleColorMode: () => void;
};

export type SolverResponse = {
  context: Record<string, unknown> & { mode?: 'bronze' | 'standard' };
  meta: {
    enabled: boolean;
    weights: {
      w_win: number;
      w_avg: number;
      w_freq: number;
    };
    unit_stats?: Record<string, { avg?: number; win?: number; freq?: number }>;
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

export type MappingFieldOptions = {
  enumOptions?: { value: number; label: string }[];
  min?: number;
  heading?: string;
  searchPlaceholder?: string;
  imageType?: 'trait' | 'emblem' | 'champion';
  unlockableValues?: string[];
  championCosts?: Record<string, number>;
};
