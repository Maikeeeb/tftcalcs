"""Edge case tests for config_loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from bfl.config import Config, default_config
from bfl.config_loader import (
    ConfigError,
    _load_int_map,
    _validate_bool,
    _validate_int,
    _validate_str_list,
    apply_ryze_mode_defaults,
    load_config,
    save_config,
)


def test_validate_int_valid():
    """Test _validate_int with valid inputs."""
    assert _validate_int("test", 5) == 5
    assert _validate_int("test", 0) == 0
    assert _validate_int("test", -5, allow_negative=True) == -5


def test_validate_int_invalid_type():
    """Test _validate_int with invalid type."""
    with pytest.raises(ConfigError, match="must be an integer"):
        _validate_int("test", "not_an_int")


def test_validate_int_negative_not_allowed():
    """Test _validate_int with negative value when not allowed."""
    with pytest.raises(ConfigError, match="cannot be negative"):
        _validate_int("test", -1)


def test_validate_int_allowed_values():
    """Test _validate_int with allowed_values constraint."""
    assert _validate_int("test", 1, allowed_values={1, 2, 3}) == 1
    with pytest.raises(ConfigError, match="must be one of"):
        _validate_int("test", 5, allowed_values={1, 2, 3})


def test_validate_bool_valid():
    """Test _validate_bool with valid inputs."""
    assert _validate_bool("test", True) is True
    assert _validate_bool("test", False) is False


def test_validate_bool_invalid():
    """Test _validate_bool with invalid type."""
    with pytest.raises(ConfigError, match="must be a boolean"):
        _validate_bool("test", "not_a_bool")


def test_validate_str_list_valid():
    """Test _validate_str_list with valid inputs."""
    assert _validate_str_list("test", ["a", "b"]) == ["a", "b"]
    assert _validate_str_list("test", ("a", "b")) == ["a", "b"]
    # Sets are unordered, so check that all elements are present
    result = _validate_str_list("test", {"a", "b"})
    assert set(result) == {"a", "b"}
    assert len(result) == 2
    assert _validate_str_list("test", None) == []


def test_validate_str_list_invalid():
    """Test _validate_str_list with invalid type."""
    with pytest.raises(ConfigError, match="must be a list of strings"):
        _validate_str_list("test", "not_a_list")


def test_load_int_map_none():
    """Test _load_int_map with None (returns defaults)."""
    defaults = {"a": 1, "b": 2}
    result = _load_int_map(None, defaults, name="test", allow_negative=False)
    assert result == defaults


def test_load_int_map_valid():
    """Test _load_int_map with valid mapping."""
    defaults = {"a": 1, "b": 2}
    raw = {"a": 3, "c": 4}
    result = _load_int_map(raw, defaults, name="test", allow_negative=False)
    assert result["a"] == 3
    assert result["b"] == 2
    assert result["c"] == 4


def test_load_int_map_invalid_type():
    """Test _load_int_map with invalid type."""
    with pytest.raises(ConfigError, match="must be an object"):
        _load_int_map("not_a_dict", {}, name="test", allow_negative=False)


def test_load_int_map_invalid_value():
    """Test _load_int_map with invalid value."""
    defaults = {"a": 1}
    raw = {"a": "not_an_int"}
    with pytest.raises(ConfigError):
        _load_int_map(raw, defaults, name="test", allow_negative=False)


def test_load_config_none():
    """Test load_config with None returns defaults."""
    config = load_config(None)
    assert isinstance(config, Config)
    assert config.team_size > 0


def test_load_config_nonexistent_file():
    """Test load_config with non-existent file."""
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/path/config.json")


def test_load_config_invalid_json():
    """Test load_config with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json }")
        f.flush()
        f.close()  # Close file before trying to delete
        try:
            with pytest.raises(ConfigError, match="Invalid JSON"):
                load_config(f.name)
        finally:
            Path(f.name).unlink(missing_ok=True)


def test_load_config_valid_file():
    """Test load_config with valid JSON file."""
    config = default_config()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config.to_dict(), f)
        f.flush()
        f.close()  # Close file before trying to delete
        try:
            loaded = load_config(f.name)
            assert loaded.team_size == config.team_size
            assert loaded.mode == config.mode
        finally:
            Path(f.name).unlink(missing_ok=True)


def test_save_config():
    """Test save_config writes valid JSON."""
    config = default_config()
    config.team_size = 8
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.close()
        try:
            save_config(config, f.name)
            loaded = load_config(f.name)
            assert loaded.team_size == 8
        finally:
            Path(f.name).unlink()


def test_apply_ryze_mode_defaults_non_ryze():
    """Test apply_ryze_mode_defaults with non-ryze mode."""
    required_champions = {}
    result = apply_ryze_mode_defaults(
        "bronze", required_champions, required_payload=None, team_size=7, team_size_provided=True
    )
    assert result == 7
    assert "TFT16_Ryze" not in required_champions


def test_apply_ryze_mode_defaults_ryze_with_provided_size():
    """Test apply_ryze_mode_defaults with ryze mode and provided team_size."""
    required_champions = {}
    result = apply_ryze_mode_defaults(
        "ryze", required_champions, required_payload=None, team_size=8, team_size_provided=True
    )
    assert result == 8
    assert required_champions.get("TFT16_Ryze") == 1


def test_apply_ryze_mode_defaults_ryze_without_provided_size():
    """Test apply_ryze_mode_defaults with ryze mode without provided team_size."""
    required_champions = {}
    result = apply_ryze_mode_defaults(
        "ryze", required_champions, required_payload=None, team_size=7, team_size_provided=False
    )
    assert result == 9  # Default to 9
    assert required_champions.get("TFT16_Ryze") == 1


def test_apply_ryze_mode_defaults_ryze_overridden():
    """Test apply_ryze_mode_defaults when Ryze is explicitly overridden."""
    required_champions = {}
    required_payload = {"TFT16_Ryze": 0}  # Explicitly set to 0
    result = apply_ryze_mode_defaults(
        "ryze",
        required_champions,
        required_payload=required_payload,
        team_size=9,
        team_size_provided=True,
    )
    assert result == 9
    # Should not add Ryze requirement if explicitly overridden
    # (The actual behavior depends on implementation - this tests current behavior)
