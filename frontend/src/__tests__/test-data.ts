import type {
  SolverResponse,
  ItemizationConfig,
  ItemizationReference,
  ItemizationRunResponse,
  ItemizationCandidate,
  ConfigData,
} from '../types';

export const mockSolverResponse: SolverResponse = {
  context: { mode: 'bronze' },
  meta: {
    enabled: true,
    weights: { w_win: 1, w_avg: 1, w_freq: 1 },
    unit_stats: {
      TFT16_Tristana: { win: 0.4, freq: 0.6, avg: 2.3, items: ['Sunfire Cape'] },
      TFT16_Lulu: { win: 0.3, freq: 0.3, avg: 3.1, items: ['Jeweled Gauntlet'] },
    },
    trait_stats_enabled: true,
  },
  solution: {
    team: ['TFT16_Tristana', 'TFT16_Lulu', 'TFT16_Teemo'],
    emblems: { Invoker: 1 },
    team_power: 10,
    bronze_count: 1,
    trait_counts: { Invoker: 2, Yordle: 2 },
    bronze_traits: ['Invoker'],
    active_traits: ['Invoker', 'Yordle'],
    upgraded_traits: [],
    used_traits: ['Invoker', 'Yordle'],
    trait_metatft: {
      Invoker: { required: 2, tier: 'S', avg: 4.2, win: 5.1, freq: 6.3 },
    },
  },
  units: {
    TFT16_Tristana: {
      traits: ['Invoker', 'Yordle'],
      cost: 1,
      metatft: { win: 0.4, freq: 0.6, avg: 2.3, items: ['Sunfire Cape'] },
    },
    TFT16_Lulu: {
      traits: ['Invoker', 'Yordle'],
      cost: 2,
      metatft: { win: 0.3, freq: 0.3, avg: 3.1, items: ['Jeweled Gauntlet'] },
    },
    TFT16_Teemo: {
      traits: ['Invoker', 'Yordle'],
      cost: 1,
      metatft: { win: 0.2, freq: 0.2, avg: 4.2 },
    },
  },
  requirements: {
    champions: {
      TFT16_Tristana: { rule: 1, present: true, status: 'ok', satisfied: true },
      TFT16_Lulu: { rule: 0, present: true, status: 'ok', satisfied: true },
    },
    traits: { Invoker: { minimum: 1, actual: 2, satisfied: true } },
    all_satisfied: true,
  },
};

export const mockStandardResponse: SolverResponse = {
  ...mockSolverResponse,
  context: { mode: 'standard' },
  solution: {
    ...mockSolverResponse.solution,
    bronze_count: 0,
    bronze_traits: [],
  },
};

export const mockRyzeResponse: SolverResponse = {
  ...mockSolverResponse,
  context: { mode: 'ryze' },
  solution: {
    ...mockSolverResponse.solution,
    bronze_traits: ['Bilgewater'],
    trait_counts: { Bilgewater: 3, Invoker: 2 },
  },
};

export const mockConfigData: ConfigData = {
  required_champions: {
    TFT16_Tristana: 1,
    TFT16_Lulu: 0,
  },
  required_traits_min: {
    Invoker: 1,
  },
  emblem_start_counts: {
    Invoker: 0,
  },
  mode: 'standard',
  must_have_itemized_tank: false,
};

export const mockItemizationReference: ItemizationReference = {
  components: [
    { apiName: 'BF_Sword', name: 'B.F. Sword' },
    { apiName: 'Recurve_Bow', name: 'Recurve Bow' },
    { apiName: 'Needlessly_Large_Rod', name: 'Needlessly Large Rod' },
  ],
  completed_items: [
    { apiName: 'Infinity_Edge', name: 'Infinity Edge', components: ['BF_Sword', 'BF_Sword'] },
    { apiName: 'Rapid_Firecannon', name: 'Rapid Firecannon', components: ['Recurve_Bow', 'Recurve_Bow'] },
  ],
  target_carries: [
    { apiName: 'TFT16_Tristana', name: 'Tristana' },
    { apiName: 'TFT16_Lulu', name: 'Lulu' },
  ],
  traits: ['Invoker', 'Yordle'],
};

export const mockItemizationCandidate: ItemizationCandidate = {
  champion: 'TFT16_Tristana',
  cost: 1,
  traits: ['Invoker', 'Yordle'],
  ideal_items: ['Infinity_Edge', 'Rapid_Firecannon', 'Jeweled_Gauntlet'],
  missing_components: ['BF_Sword'],
  trait_shells: ['Invoker'],
  team_trait_matches: ['Yordle'],
  needed_trait_matches: ['Invoker'],
  suggested_slams: ['Rapid_Firecannon'],
  score: {
    full_items: 2,
    completed_items: 1,
    reforged_items: 0,
    craftable_items: 1,
    partial_components: 1,
    matched_completed: ['Infinity_Edge'],
    reforged: [],
    craftable: ['Rapid_Firecannon'],
    partial: [{ item: 'Jeweled_Gauntlet', components_hit: 1, missing_components: ['BF_Sword'] }],
    needed_trait_hits: 1,
    team_trait_hits: 1,
  },
};

export const mockItemizationResponse: ItemizationRunResponse = {
  version: 2,
  result: {
    context: {
      mode: 'itemization',
      set_id: 'TFT_Set16',
      available_components: ['BF_Sword', 'Recurve_Bow'],
      available_completed_items: ['Infinity_Edge'],
      team_traits: ['Yordle'],
      needed_traits: ['Invoker'],
      allow_reforge: false,
    },
    solution: {
      ranked_candidates: [mockItemizationCandidate],
    },
    items: {
      components: ['BF_Sword', 'Recurve_Bow'],
      completed_items: ['Infinity_Edge'],
      names_by_api: {
        BF_Sword: 'B.F. Sword',
        Recurve_Bow: 'Recurve Bow',
        Infinity_Edge: 'Infinity Edge',
        Rapid_Firecannon: 'Rapid Firecannon',
        Jeweled_Gauntlet: 'Jeweled Gauntlet',
      },
    },
  },
};

export const mockItemizationConfig: ItemizationConfig = {
  available_components: ['BF_Sword', 'Recurve_Bow'],
  available_completed_items: ['Infinity_Edge'],
  target_carries: ['TFT16_Tristana'],
  team_traits: ['Yordle'],
  needed_traits: ['Invoker'],
  allow_reforge: false,
};
