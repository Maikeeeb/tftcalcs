# Bronze-for-Life mode: current behavior

This document summarizes how Bronze-for-Life now evaluates teams and emblems after the value-alignment changes.

## Hard validity gates

A state is considered valid only if **all** of the following are met:

- At least **6 bronze traits** can be achieved (states that cannot reach 6 given remaining slots are pruned).
- At least **one quality tank** and **one quality carry** are present (quality is power-based and normally requires an active trait).
- Traitless champions (no eligible traits) may count as quality tanks/carries based on power alone; champions that *have* eligible traits still need at least one active trait.
- Required-one-of and required trait minimums remain satisfied/feasible.

Invalid states stay in the beam only as low-priority expansions; any valid state outranks invalid ones.

## Bronze scoring with diminishing returns

Bronze count is no longer linear. The piecewise score used by the sorter is:

| Bronze traits | Score |
| --- | --- |
| <6 | −∞ (invalid) |
| 6 | 100 |
| 7 | 160 |
| 8 | 200 |
| 9 | 215 |
| ≥10 | 225 |

This captures “6 is mandatory, 7–8 are big gains, 9+ are nice-to-have”.

## Quality anchors

- A **quality unit** is any champion whose MetaTFT-derived power is above the 7th-best unit in the pool **and** that has at least one active trait.
- **Quality threshold calculation**: Power values of all playable champions are sorted in descending order. The threshold is set to the power of the 7th-best unit (or the 6th if fewer than 7 units exist). This ensures roughly the top 6-7 units qualify as "quality."
- **Tank quality threshold**: If tank champions are identified from MetaTFT data, the tank threshold is set to the minimum of the carry threshold and the maximum tank power. This allows tanks to qualify even if they're slightly below the general quality threshold.
- Tanks are identified from MetaTFT item builds; if no tank labels exist, all quality units count as tanks *and* carries for feasibility.
- The scorer requires at least one quality tank and one quality carry; their combined power forms the primary quality score.
- Quality units with no active traits mark the state invalid (they violate the “activate at least one trait” rule).

## Fake bronze penalty

For each bronze-tier trait whose contributing units are all below the quality threshold, a small penalty is applied. Bronze traits with at least one quality unit are never penalized.

## Tie-breakers and trait stats

- The sort key order is: validity → required-one-of satisfaction → trait minimums → bronze piecewise score → quality score → fake-bronze penalty (lower is better) → MetaTFT trait score (tie-breaker only) → active count → bronze count → fewer upgraded traits → raw team power.
- Trait stats are **only** used as a late tie-breaker and to allow sensible emblem choices; they never outrank bronze count or quality anchors.

## Emblem selection

Auto-emblem selection now mirrors the same validity/quality rules. Emblems that break validity (dropping below 6 bronze or losing a quality anchor) are rejected in favor of those that strengthen quality or bronze counts.

**Emblem selection algorithm**: The `choose_best_emblems` function uses a greedy selection algorithm. Starting with fixed emblems (`emblem_start_counts`), it iteratively evaluates each candidate emblem from `auto_candidates` and selects the one that maximizes the team's overall score. The evaluation considers bronze count, trait scores, quality units, requirement satisfaction, and validity gates. Emblems that would break validity (drop below 6 bronze or lose quality anchors) are rejected. The algorithm respects `max_emblems_total` to limit total emblem count.
