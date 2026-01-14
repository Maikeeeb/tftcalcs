"""Edge case tests for solver_api module."""

import pytest

from bfl.config import Config, default_config
from bfl.solver_api import SolverError, _resolve_config, run_bfl


def test_resolve_config_with_config_object():
    """Test _resolve_config with a Config object."""
    config = default_config()
    result = _resolve_config(config, None)
    assert result is config


def test_resolve_config_with_config_path_none():
    """Test _resolve_config with config_path=None."""
    result = _resolve_config(None, None)
    assert isinstance(result, Config)


def test_resolve_config_with_config_path():
    """Test _resolve_config with a config_path."""
    from bfl.config_loader import ConfigError

    # This will try to load from the path, but if file doesn't exist, it raises ConfigError
    with pytest.raises(ConfigError, match="not found"):
        _resolve_config(None, "/nonexistent/path.json")


def test_run_bfl_with_tank_requirement():
    """Test run_bfl with must_have_itemized_tank=True."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = True

    # This should work if MetaTFT data is available
    try:
        result = run_bfl(config)
        assert "requirements" in result
        assert "tank" in result["requirements"]
        tank_req = result["requirements"]["tank"]
        if tank_req:
            assert "required" in tank_req
            assert "satisfied" in tank_req
    except RuntimeError as e:
        # If no tank champions found, that's expected behavior
        if "no tank champions" not in str(e):
            raise


def test_run_bfl_tank_requirement_no_tanks():
    """Test run_bfl error when must_have_itemized_tank=True but no tanks found."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = True
    # Use a path that won't have MetaTFT data or empty file
    from pathlib import Path
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("")  # Empty MetaTFT file
        f.flush()
        f.close()
        config.metatft_txt_path = Path(f.name)
        try:
            with pytest.raises(RuntimeError, match="no tank champions"):
                run_bfl(config)
        finally:
            Path(f.name).unlink(missing_ok=True)


def test_run_solver_itemization_error_handling():
    """Test run_solver handles ItemizationError correctly."""
    from bfl.solver_api import run_solver
    from bfl.itemization_solver import ItemizationError

    config = default_config()
    config.mode = "itemization"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    # Invalid config that might cause ItemizationError
    config.available_components = []
    config.target_carries = []

    # This should either work or raise SolverError (wrapping ItemizationError)
    try:
        result = run_solver(config)
        assert "solution" in result
    except SolverError:
        # Expected if itemization fails
        pass
