"""Integration tests for solver API functions."""

import pytest

from bfl.config import Config, default_config
from bfl.solver_api import SolverError, run_bfl, run_solver

pytestmark = pytest.mark.integration


def test_run_bfl_with_default_config():
    """Test run_bfl with default configuration."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    # Verify result structure
    assert "solution" in result
    assert "context" in result
    assert "debug_log" in result
    assert "meta" in result
    assert "units" in result
    assert "requirements" in result

    # Verify solution content
    solution = result["solution"]
    assert "team" in solution
    assert "bronze_count" in solution
    assert "trait_counts" in solution
    assert isinstance(solution["team"], list)
    assert len(solution["team"]) <= config.team_size


def test_run_bfl_bronze_mode():
    """Test run_bfl specifically in bronze mode."""
    config = default_config()
    config.mode = "bronze"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    assert result["solution"]["bronze_count"] >= 0
    assert "bronze_traits" in result["solution"]


def test_run_bfl_standard_mode():
    """Test run_bfl in standard mode."""
    config = default_config()
    config.mode = "standard"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    # Standard mode should still work
    assert "solution" in result
    assert "team" in result["solution"]


def test_run_bfl_ryze_mode():
    """Test run_bfl in ryze mode."""
    config = default_config()
    config.mode = "ryze"
    config.team_size = 9
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    # Ryze mode should work
    assert "solution" in result
    assert "context" in result
    # Ryze mode context should include region traits
    if "region_traits" in result["context"]:
        assert isinstance(result["context"]["region_traits"], list)


def test_run_solver_bronze_mode():
    """Test run_solver with bronze mode."""
    config = default_config()
    config.mode = "bronze"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_solver(config)

    assert "solution" in result
    assert result["solution"]["bronze_count"] >= 0


def test_run_solver_itemization_mode():
    """Test run_solver with itemization mode."""
    config = default_config()
    config.mode = "itemization"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.available_components = ["B.F. Sword"]

    result = run_solver(config)

    assert "solution" in result
    assert "ranked_candidates" in result["solution"]


def test_run_bfl_with_emblems():
    """Test run_bfl with emblem configuration."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.emblem_start_counts = {"Demacia": 1}
    config.max_emblems_total = 2

    result = run_bfl(config)

    assert "solution" in result
    assert "emblems" in result["solution"]
    assert isinstance(result["solution"]["emblems"], dict)


def test_run_bfl_with_required_champions():
    """Test run_bfl with required champions."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    # Get a valid champion name from the config
    if config.required_champions:
        champ_name = next(iter(config.required_champions.keys()))
        config.required_champions = {champ_name: 1}  # Require this champion

        result = run_bfl(config)

        assert "solution" in result
        assert "requirements" in result
        # Check that required champion is in the team or requirements show it
        assert (
            champ_name in result["solution"]["team"] or not result["requirements"]["all_satisfied"]
        )


def test_run_bfl_error_handling():
    """Test run_bfl error handling with invalid configuration."""
    config = default_config()
    config.team_size = 1000  # Unrealistically large team size

    with pytest.raises((SolverError, RuntimeError)):
        run_bfl(config)


def test_run_bfl_debug_log():
    """Test that debug_log is populated."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    assert "debug_log" in result
    assert isinstance(result["debug_log"], list)
    assert len(result["debug_log"]) > 0


def test_run_bfl_context_details():
    """Test that context contains expected details."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    assert "context" in result
    context = result["context"]
    assert "team_size" in context
    assert "beam_width" in context
    assert "mode" in context
    assert context["team_size"] == config.team_size


def test_run_bfl_requirements_satisfaction():
    """Test that requirements satisfaction is reported."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    result = run_bfl(config)

    assert "requirements" in result
    requirements = result["requirements"]
    assert "champions" in requirements
    assert "traits" in requirements
    assert "all_satisfied" in requirements
    assert isinstance(requirements["all_satisfied"], bool)
