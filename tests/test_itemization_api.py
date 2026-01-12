import pytest

fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from ui_api.main import app


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
