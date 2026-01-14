# Standard mode: MetaTFT trait-first optimization

This document explains how Standard mode evaluates teams and differs from Bronze-for-Life mode.

## Primary Objective

Standard mode optimizes for **MetaTFT trait scores** (`trait_score`) as the primary objective, rather than maximizing bronze trait count. This makes it a trait-first optimization approach, prioritizing teams with the highest combined trait statistics from MetaTFT data.

## Sort Key Structure

Standard mode uses the same sort key structure as bronze mode, but with `trait_stats` enabled (resulting in non-zero `trait_score` values). The sort key tuple is:

```
(valid, -missing_required_one, -missing_requirements, bronze_score, quality_score, -penalty, trait_score, active, bronze, -upgraded, power)
```

Where:
- `valid` - Boolean (1 if valid, 0 if invalid)
- `missing_required_one` - Number of required "one-of" units missing (negated for sorting)
- `missing_requirements` - Number of unsatisfied trait minimums (negated for sorting)
- `bronze_score` - Piecewise bronze score (100-225 for 6-10+ bronze traits)
- `quality_score` - Combined power of quality tanks and carries
- `penalty` - Fake bronze penalty (negated, so lower penalty is better)
- `trait_score` - **MetaTFT trait score (primary in standard mode)**
- `active` - Count of active eligible traits
- `bronze` - Raw bronze count
- `upgraded` - Count of upgraded traits (negated, so fewer is better)
- `power` - Raw team power from MetaTFT

## Ranking Differences

### Bronze Mode
- `trait_score` is typically 0 (trait_stats disabled)
- `bronze_score` dominates ranking after validity/requirements
- Teams are ranked primarily by bronze count (with piecewise scoring)

### Standard Mode
- `trait_score` is non-zero (trait_stats enabled from `data/metatft_traits.txt`)
- `trait_score` becomes the primary ranking factor after validity/requirements
- Teams are ranked primarily by MetaTFT trait statistics
- Bronze count still matters but is secondary to trait scores

## Validity Gates

Standard mode respects the same validity gates as bronze mode:

- At least **6 bronze traits** must be achievable
- At least **one quality tank** and **one quality carry** must be present
- Quality units must activate at least one trait (unless traitless)
- Required trait minimums and champion requirements must be satisfied

Invalid states are deprioritized in the beam search, just like in bronze mode.

## Quality Anchors

Standard mode uses the same quality anchor system:

- Quality threshold = power of 7th-best unit (or 6th if fewer than 7 units)
- Tank quality threshold may be lower (minimum of carry threshold and max tank power)
- Quality units must activate at least one trait (unless traitless)
- Combined quality score (tanks + carries) influences ranking

## Fake Bronze Penalties

Standard mode applies the same fake bronze penalties as bronze mode:

- Bronze traits with all low-quality units receive a penalty
- Bronze traits with at least one quality unit are never penalized
- Penalty is negated in sort key (lower penalty = better)

## Trait Statistics

Trait statistics are loaded from `data/metatft_traits.txt` when available. These include:

- Win rate (`win`) - How often teams with this trait win
- Average placement (`avg`) - Average placement of teams with this trait
- Frequency (`freq`) - How often this trait appears in top teams

The `trait_score` is computed using these statistics weighted by `w_win`, `w_avg`, and `w_freq` config values. In standard mode, this score heavily influences team ranking.

## When to Use Standard Mode

Use standard mode when:
- You want to optimize for MetaTFT trait statistics rather than bronze count
- You're looking for teams that perform well according to live game data
- You want trait-first optimization that considers win rates and placements

Use bronze mode when:
- You want to maximize the number of bronze traits
- You're playing Bronze-for-Life style challenges
- Bronze count is more important than trait statistics
