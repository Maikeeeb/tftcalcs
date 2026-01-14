"""Integration tests for FastAPI endpoints."""

import pytest

from fastapi import status
from fastapi.testclient import TestClient

from bfl.config import default_config
from ui_api.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_schema_endpoint(client):
    """Test that the schema endpoint returns valid JSON schema."""
    response = client.get("/schema")
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert isinstance(schema, dict)
    assert "properties" in schema or "$schema" in schema


def test_config_endpoint(client):
    """Test that the config endpoint returns default configuration."""
    response = client.get("/config")
    assert response.status_code == status.HTTP_200_OK
    config = response.json()
    assert isinstance(config, dict)
    assert "team_size" in config
    assert "beam_width" in config
    assert "mode" in config


def test_run_endpoint_with_valid_config(client):
    """Test the /run endpoint with a valid bronze mode configuration."""
    config = default_config().to_dict()
    config["team_size"] = 5
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    response = client.post("/run", json=config)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "solution" in result
    assert "team" in result["solution"]
    assert isinstance(result["solution"]["team"], list)


def test_run_endpoint_with_invalid_config(client):
    """Test the /run endpoint with invalid configuration."""
    invalid_config = {"team_size": "not_a_number"}

    response = client.post("/run", json=invalid_config)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_itemization_schema_endpoint(client):
    """Test the itemization schema endpoint."""
    response = client.get("/v2/itemization/schema")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "schema" in data


def test_itemization_config_endpoint(client):
    """Test the itemization config endpoint."""
    response = client.get("/v2/itemization/config")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "config" in data
    assert data["config"]["mode"] == "itemization"


def test_itemization_data_endpoint(client):
    """Test the itemization reference data endpoint."""
    response = client.get("/v2/itemization/data")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "data" in data
    assert "components" in data["data"]


def test_itemization_run_endpoint(client):
    """Test the itemization run endpoint."""
    payload = {
        "version": 2,
        "config": {
            "mode": "itemization",
            "available_components": ["B.F. Sword", "Sparring Gloves"],
            "available_completed_items": [],
            "target_carries": [],
            "team_traits": [],
            "needed_traits": [],
            "allow_reforge": False,
            "must_have_itemized_tank": False,
        },
    }

    response = client.post("/v2/itemization/run", json=payload)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "version" in result
    assert "result" in result
    assert "solution" in result["result"]


def test_itemization_run_endpoint_invalid_version(client):
    """Test itemization endpoint with wrong version."""
    payload = {
        "version": 1,  # Wrong version
        "config": {
            "mode": "itemization",
        },
    }

    response = client.post("/v2/itemization/run", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_itemization_run_endpoint_missing_config(client):
    """Test itemization endpoint with missing config."""
    payload = {
        "version": 2,
    }

    response = client.post("/v2/itemization/run", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_run_endpoint_ryze_mode(client):
    """Test the /run endpoint with ryze mode."""
    config = default_config().to_dict()
    config["mode"] = "ryze"
    config["team_size"] = 9
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    response = client.post("/run", json=config)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "solution" in result
    assert "team" in result["solution"]


def test_run_endpoint_standard_mode(client):
    """Test the /run endpoint with standard mode."""
    config = default_config().to_dict()
    config["mode"] = "standard"
    config["team_size"] = 5
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    response = client.post("/run", json=config)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "solution" in result
    assert "team" in result["solution"]
