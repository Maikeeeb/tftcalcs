# tftcalcs

## Features

- Optimizes "Bronze for Life" trait activations using a beam-search solver that respects team size limits and trait blacklists.
- Loads official TFT set data from `en_us.json` with helper utilities for champions, traits, and breakpoints.
- Supports emblem modeling, including fixed starting emblems and optional automatic emblem assignment with configurable caps.
- Integrates MetaTFT stats (win rate, average placement, frequency) as a tie-breaker to prefer stronger lineups.
- Provides normalization and parsing helpers for MetaTFT unit data, including power calculations for each champion.
- Includes a command-line entry point (`bfl.bronze_for_life:main`) that prints optimized teams and trait summaries.

