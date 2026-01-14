"""Shared fixtures for integration tests."""

import sys
from pathlib import Path

import pytest

# Ensure the project root is importable
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Skip integration tests if dependencies are missing
fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from bfl.config import Config, default_config
from ui_api.main import app


@pytest.fixture
def test_client():
    """FastAPI test client for integration tests."""
    return TestClient(app)


@pytest.fixture
def default_config_dict():
    """Return default config as a dictionary."""
    return default_config().to_dict()


@pytest.fixture
def minimal_bronze_config():
    """Minimal valid config for bronze mode."""
    config = default_config()
    config.team_size = 5
    config.beam_width = 50
    config.max_emblems_total = 0
    config.must_have_itemized_tank = False
    return config.to_dict()


@pytest.fixture
def minimal_itemization_config():
    """Minimal valid config for itemization mode."""
    config = default_config()
    config.mode = "itemization"
    config.team_size = 5
    config.beam_width = 50
    config.must_have_itemized_tank = False
    config.available_components = ["B.F. Sword"]
    config.target_carries = []
    return config.to_dict()
