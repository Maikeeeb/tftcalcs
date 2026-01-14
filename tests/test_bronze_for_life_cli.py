"""Tests for bronze_for_life CLI entry point."""

import io
from unittest.mock import patch

import pytest

from bfl.bronze_for_life import main
from bfl.config import default_config


def test_main_with_config_object():
    """Test main() function with a Config object."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    # Capture stdout
    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    assert "Loaded set" in output
    assert "TEAM_SIZE=5" in output
    assert "Bronze-active eligible trait count" in output or "Result" in output


def test_main_with_config_path_none():
    """Test main() function with config_path=None (uses defaults)."""
    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        # This will use default config
        main(config_path=None)

    output = captured_output.getvalue()
    # Should produce some output
    assert len(output) > 0


def test_main_itemization_mode():
    """Test main() function with itemization mode."""
    config = default_config()
    config.mode = "itemization"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.available_components = ["B.F. Sword"]

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    assert "itemization mode" in output
    assert (
        "Itemization ranking" in output
        or "ranked_candidates" in output
        or "Available components" in output
    )


def test_main_ryze_mode():
    """Test main() function with ryze mode."""
    config = default_config()
    config.mode = "ryze"
    config.team_size = 9
    config.beam_width = 50
    config.must_have_itemized_tank = False

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    assert (
        "Ryze mode" in output
        or "region traits" in output
        or "Optimizing for MAX active region traits" in output
    )


def test_main_standard_mode():
    """Test main() function with standard mode."""
    config = default_config()
    config.mode = "standard"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    assert "Standard mode" in output or "Result" in output


def test_main_with_required_champions():
    """Test main() function with required champions."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    # Set a required champion if available
    if config.required_champions:
        champ_name = next(iter(config.required_champions.keys()))
        config.required_champions = {champ_name: 1}

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    # Should show constraints if champions are required
    assert len(output) > 0


def test_main_with_emblems():
    """Test main() function with emblems configured."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.emblem_start_counts = {"Demacia": 1}
    config.max_emblems_total = 2

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    assert "Hard emblems" in output or "Emblem starting counts" in output


def test_print_itemization_result():
    """Test _print_itemization_result function indirectly through main."""
    config = default_config()
    config.mode = "itemization"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.available_components = ["B.F. Sword", "Sparring Gloves"]
    config.target_carries = []

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        main(config=config)

    output = captured_output.getvalue()
    # Should show itemization output
    assert (
        "itemization" in output.lower()
        or "ranking" in output.lower()
        or "components" in output.lower()
    )
