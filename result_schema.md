# `run_bfl` result schema

The solver exposes a callable API:

```python
from bfl.solver_api import run_bfl
result: dict[str, object] = run_bfl(config)
```

The returned dictionary is stable and UI-friendly. Images can be layered on top of these text-first values without changing the shape.

## Top-level keys

- `context`: Metadata about the run (set ID, configuration highlights, breakpoints, etc.).
- `meta`: MetaTFT usage and weights, plus any per-unit stats when available.
- `solution`: Final solver output (team, traits, counts, emblems, scoring).
- `units`: Per-unit details for the champions present in the final team.
- `requirements`: Satisfaction details for champion and trait constraints.

## `context`

```json
{
  "set_id": "TFT_SET_ID",
  "json_path": "path/to/set.json",
  "team_size": 8,
  "beam_width": 200,
  "blacklist_traits": ["Deadeye", "Heavenly"],
  "eligible_traits": ["Bruiser", "Sniper"],
  "trait_breakpoints": {"Bruiser": [2, 4, 6]},
  "trait_frequency": {"Bruiser": 12},
  "champion_count": 58,
  "trait_breakpoint_count": 31,
  "emblem_start_counts": {"Bruiser": 1},
  "max_emblems_total": 2
}
```

## `meta`

```json
{
  "enabled": true,
  "weights": {"w_win": 3.0, "w_avg": 1.0, "w_freq": 0.5},
  "unit_stats": {
    "TFT16_Example": {"avg": 3.5, "win": 0.12, "freq": 0.45}
  }
}
```

`enabled` is `false` and `unit_stats` is `None` when no MetaTFT paste is provided.

## `solution`

```json
{
  "team": ["TFT16_UnitA", "TFT16_UnitB"],
  "emblems": {"Bruiser": 1},
  "team_power": 12.34,
  "bronze_count": 5,
  "trait_counts": {"Bruiser": 4, "Sniper": 2},
  "bronze_traits": ["Bruiser"],
  "active_traits": ["Bruiser", "Sniper"],
  "upgraded_traits": ["Bruiser"],
  "used_traits": ["Bruiser", "Sniper", "Traveler"]
}
```

- `bronze_traits` are eligible traits that reach only the first tier.
- `active_traits` are eligible traits that reach any tier.
- `upgraded_traits` are eligible traits that reach tier 2+ (not bronze).
- `used_traits` lists all traits appearing on the team before eligibility filtering.

## `units`

Per champion present in the final team:

```json
{
  "TFT16_UnitA": {"traits": ["Bruiser"], "cost": 3, "metatft": {"avg": 3.5, "win": 0.12, "freq": 0.45}},
  "TFT16_UnitB": {"traits": ["Sniper"], "cost": 4, "metatft": null}
}
```

`metatft` mirrors the `meta.unit_stats` entry when available.

## `requirements`

```json
{
  "champions": {
    "TFT16_UnitA": {"rule": 1, "present": true, "status": "required", "satisfied": true},
    "TFT16_UnitZ": {"rule": -1, "present": false, "status": "banned", "satisfied": true}
  },
  "traits": {
    "Bruiser": {"minimum": 2, "actual": 4, "satisfied": true}
  },
  "all_satisfied": true
}
```

- `rule`: `1` = must include, `-1` = must exclude, `0` = ignored.
- `minimum`: Desired minimum stacks for a trait; `actual` reflects the solved team.
- `all_satisfied`: True only when every requirement is met.
