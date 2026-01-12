import pytest

fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from bfl.config import default_config
from ui_api.main import app, run_solver_endpoint


def test_itemization_v2_run_endpoint():
    client = TestClient(app)
    payload = {
        "version": 2,
        "config": {
            "mode": "itemization",
            "available_components": ["B.F. Sword", "Sparring Gloves"],
            "available_completed_items": [],
            "target_carries": ["TFT16_Jinx", "TFT16_Ahri"],
            "team_traits": [],
            "needed_traits": [],
            "allow_reforge": False,
        },
    }

    response = client.post("/v2/itemization/run", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    assert "result" in body
    assert body["result"]["solution"]["ranked_candidates"]


def test_run_solver_accepts_config_object():
    config = default_config()
    config.mode = "itemization"
    config.available_components = ["Needlessly Large Rod", "Needlessly Large Rod"]
    config.target_carries = ["TFT16_Ahri"]

    result = run_solver_endpoint(config)

    assert result["solution"]["ranked_candidates"]
