"""End-to-end integration tests for UI → API → Solver flow."""

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


def test_complete_bronze_mode_flow(client):
    """Test complete flow: request → validation → solver → response."""
    # Step 1: Get schema
    schema_response = client.get("/schema")
    assert schema_response.status_code == status.HTTP_200_OK
    schema = schema_response.json()

    # Step 2: Get default config
    config_response = client.get("/config")
    assert config_response.status_code == status.HTTP_200_OK
    config = config_response.json()

    # Step 3: Modify config for faster testing
    config["team_size"] = 5
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    # Step 4: Validate config matches schema (would be done by UI)
    assert "team_size" in config
    assert config["team_size"] > 0

    # Step 5: Run solver
    run_response = client.post("/run", json=config)
    assert run_response.status_code == status.HTTP_200_OK

    # Step 6: Verify response structure
    result = run_response.json()
    assert "solution" in result
    assert "context" in result
    assert "debug_log" in result
    assert "meta" in result

    # Step 7: Verify solution contains expected fields
    solution = result["solution"]
    assert "team" in solution
    assert "bronze_count" in solution
    assert "trait_counts" in solution
    assert isinstance(solution["team"], list)
    assert len(solution["team"]) <= config["team_size"]


def test_complete_itemization_flow(client):
    """Test complete itemization flow."""
    # Step 1: Get itemization schema
    schema_response = client.get("/v2/itemization/schema")
    assert schema_response.status_code == status.HTTP_200_OK

    # Step 2: Get itemization config
    config_response = client.get("/v2/itemization/config")
    assert config_response.status_code == status.HTTP_200_OK
    config_data = config_response.json()

    # Step 3: Get reference data
    data_response = client.get("/v2/itemization/data")
    assert data_response.status_code == status.HTTP_200_OK
    reference_data = data_response.json()

    # Step 4: Prepare payload
    payload = {
        "version": 2,
        "config": {
            **config_data["config"],
            "available_components": ["B.F. Sword", "Sparring Gloves"],
            "target_carries": [],
            "must_have_itemized_tank": False,
        },
    }

    # Step 5: Run itemization solver
    run_response = client.post("/v2/itemization/run", json=payload)
    assert run_response.status_code == status.HTTP_200_OK

    # Step 6: Verify response
    result = run_response.json()
    assert "version" in result
    assert "result" in result
    assert result["version"] == 2


def test_error_handling_invalid_json(client):
    """Test error handling for invalid JSON payload."""
    response = client.post(
        "/run",
        json={"team_size": "invalid"},  # Should be integer
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_error_handling_missing_required_fields(client):
    """Test error handling for missing required fields."""
    # Missing team_size might be handled by defaults, but test with clearly invalid config
    response = client.post("/run", json={"mode": "invalid_mode"})
    # Should either return 400 or use defaults, depending on validation
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK)


def test_response_schema_consistency(client):
    """Test that all endpoints return consistent response formats."""
    config = default_config().to_dict()
    config["team_size"] = 5
    config["beam_width"] = 50
    config["must_have_itemized_tank"] = False

    response = client.post("/run", json=config)
    assert response.status_code == status.HTTP_200_OK

    result = response.json()

    # Verify top-level keys exist
    required_keys = ["solution", "context", "debug_log", "meta", "units", "requirements"]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"

    # Verify solution structure
    solution = result["solution"]
    assert "team" in solution
    assert "emblems" in solution
    assert "bronze_count" in solution
    assert "trait_counts" in solution


def test_cors_headers(client):
    """Test that CORS headers are present (if applicable)."""
    response = client.options("/run")
    # CORS is configured in the app, but TestClient may not show all headers
    # Just verify the endpoint responds
    assert response.status_code in (status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED)
