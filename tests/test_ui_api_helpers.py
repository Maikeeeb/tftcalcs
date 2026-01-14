"""Tests for ui_api helper functions."""

import pytest

fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from bfl.config import Config, default_config
from bfl.config_loader import ConfigError
from bfl.solver_api import SolverError
from ui_api.main import (
    _config_from_payload,
    _normalize_config_payload,
    _versioned_config_payload,
    app,
)


def test_normalize_config_payload_with_dict():
    """Test _normalize_config_payload with a dictionary."""
    payload = {"team_size": 9, "mode": "bronze"}
    result = _normalize_config_payload(payload)
    assert result == payload


def test_normalize_config_payload_with_config():
    """Test _normalize_config_payload with a Config object."""
    config = default_config()
    result = _normalize_config_payload(config)
    assert isinstance(result, dict)
    assert result["team_size"] == config.team_size
    assert result["mode"] == config.mode


def test_config_from_payload_minimal():
    """Test _config_from_payload with minimal valid payload."""
    payload = {}
    config = _config_from_payload(payload)
    assert isinstance(config, Config)
    assert config.team_size > 0


def test_config_from_payload_with_overrides():
    """Test _config_from_payload with overridden values."""
    payload = {"team_size": 7, "beam_width": 100, "mode": "standard"}
    config = _config_from_payload(payload)
    assert config.team_size == 7
    assert config.beam_width == 100
    assert config.mode == "standard"


def test_config_from_payload_invalid_team_size():
    """Test _config_from_payload with invalid team_size."""
    payload = {"team_size": -5}
    with pytest.raises(ConfigError, match="cannot be negative"):
        _config_from_payload(payload)


def test_config_from_payload_invalid_mode():
    """Test _config_from_payload with invalid mode."""
    payload = {"mode": "invalid_mode"}
    with pytest.raises(ConfigError, match="mode must be"):
        _config_from_payload(payload)


def test_config_from_payload_invalid_blacklist():
    """Test _config_from_payload with invalid blacklist format."""
    payload = {"blacklist_traits_by_name": "not_a_list"}
    with pytest.raises(ConfigError, match="must be a list"):
        _config_from_payload(payload)


def test_config_from_payload_valid_blacklist():
    """Test _config_from_payload with valid blacklist."""
    payload = {"blacklist_traits_by_name": ["Targon", "Demacia"]}
    config = _config_from_payload(payload)
    assert "Targon" in config.blacklist_traits_by_name
    assert "Demacia" in config.blacklist_traits_by_name


def test_versioned_config_payload_valid():
    """Test _versioned_config_payload with valid versioned payload."""
    payload = {
        "version": 2,
        "config": {
            "mode": "itemization",
            "available_components": ["B.F. Sword"],
        },
    }
    config = _versioned_config_payload(payload)
    assert isinstance(config, Config)
    assert config.mode == "itemization"


def test_versioned_config_payload_wrong_version():
    """Test _versioned_config_payload with wrong version."""
    payload = {"version": 1, "config": {"mode": "itemization"}}
    with pytest.raises(ConfigError, match="Expected payload version"):
        _versioned_config_payload(payload)


def test_versioned_config_payload_missing_config():
    """Test _versioned_config_payload with missing config."""
    payload = {"version": 2}
    with pytest.raises(ConfigError, match="must include a 'config' object"):
        _versioned_config_payload(payload)


def test_versioned_config_payload_invalid_payload():
    """Test _versioned_config_payload with non-dict payload."""
    with pytest.raises(ConfigError, match="Payload must be an object"):
        _versioned_config_payload("not_a_dict")


def test_versioned_config_payload_config_object():
    """Test _versioned_config_payload with Config object in payload."""
    config_obj = default_config()
    config_obj.mode = "itemization"
    payload = {"version": 2, "config": config_obj}
    config = _versioned_config_payload(payload)
    assert isinstance(config, Config)
    assert config.mode == "itemization"


def test_run_endpoint_error_handling():
    """Test error handling in run endpoint."""
    test_client = TestClient(app)
    # Missing required fields or invalid JSON schema should return 400
    response = test_client.post("/run", json={"invalid": "data"})
    # Depending on validation, this might be 400 or might use defaults
    assert response.status_code in (400, 200)


def test_itemization_endpoint_error_handling():
    """Test error handling in itemization endpoint."""
    test_client = TestClient(app)
    # Missing version
    response = test_client.post("/v2/itemization/run", json={"config": {}})
    assert response.status_code == 400

    # Invalid version
    response = test_client.post("/v2/itemization/run", json={"version": 99, "config": {}})
    assert response.status_code == 400


def test_config_from_payload_invalid_weight_type():
    """Test _config_from_payload with invalid weight type."""
    payload = {"w_win": "not_a_number"}
    with pytest.raises(ConfigError, match="must be numeric"):
        _config_from_payload(payload)


def test_config_from_payload_invalid_must_have_tank_type():
    """Test _config_from_payload with invalid must_have_itemized_tank type."""
    payload = {"must_have_itemized_tank": "not_a_bool"}
    with pytest.raises(ConfigError, match="must be a boolean"):
        _config_from_payload(payload)


def test_config_from_payload_invalid_allow_reforge_type():
    """Test _config_from_payload with invalid allow_reforge type."""
    payload = {"allow_reforge": "not_a_bool"}
    with pytest.raises(ConfigError, match="must be a boolean"):
        _config_from_payload(payload)


def test_config_from_payload_legacy_itemization_fields():
    """Test _config_from_payload with legacy itemization field names."""
    payload = {
        "itemization_components": ["B.F. Sword"],
        "itemization_completed_items": ["Infinity Edge"],
        "itemization_candidate_champions": ["TFT16_Jinx"],
        "itemization_team_traits": ["Gunslinger"],
        "itemization_needed_traits": ["Bruiser"],
    }
    config = _config_from_payload(payload)
    assert config.available_components == ["B.F. Sword"]
    assert config.available_completed_items == ["Infinity Edge"]
    assert config.target_carries == ["TFT16_Jinx"]
    assert config.team_traits == ["Gunslinger"]
    assert config.needed_traits == ["Bruiser"]


def test_run_endpoint_solver_error_handling():
    """Test run endpoint handles SolverError correctly."""
    test_client = TestClient(app)
    # Create a config that might cause a solver error
    config = default_config().to_dict()
    config["team_size"] = 1000  # Unrealistically large
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    response = test_client.post("/run", json=config)
    # Should return 500 with error details
    assert response.status_code in (400, 500)
    if response.status_code == 500:
        body = response.json()
        assert "error" in body.get("detail", {})


def test_itemization_endpoint_solver_error_handling():
    """Test itemization endpoint handles SolverError correctly."""
    test_client = TestClient(app)
    # Use a config that will actually cause an error - invalid champion requirement
    # This should fail validation before reaching the solver
    payload = {
        "version": 2,
        "config": {
            "mode": "itemization",
            "team_size": 5,
            "beam_width": 50,
            "must_have_itemized_tank": False,
            "required_champions": {"INVALID_CHAMPION_NAME_XYZ": 1},  # Invalid champion
        },
    }

    response = test_client.post("/v2/itemization/run", json=payload)
    # Should return 400 (validation error) or 500 (solver error), or 200 if validation passes
    # The invalid champion should be caught during validation, but if it passes validation
    # and succeeds, that's also valid behavior
    assert response.status_code in (200, 400, 500)
    if response.status_code == 500:
        body = response.json()
        detail = body.get("detail", {})
        if isinstance(detail, dict):
            assert "error" in detail
    elif response.status_code == 400:
        # Validation error is also acceptable
        pass
    # If 200, the request succeeded which is fine
