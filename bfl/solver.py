"""Solver module - re-exports from split modules for backward compatibility."""

# Re-export main solver function and DecisionLogger
from bfl.beam_search import DecisionLogger, solve_beam_search_bronze_with_emblems

# Re-export team building functions
from bfl.team_builder import (
    build_required_team,
    compute_effective_counts,
    feasibility_check,
    requirement_gap,
)

# Re-export scoring functions
from bfl.scoring import score_state

__all__ = [
    "DecisionLogger",
    "solve_beam_search_bronze_with_emblems",
    "build_required_team",
    "compute_effective_counts",
    "feasibility_check",
    "requirement_gap",
    "score_state",
]
