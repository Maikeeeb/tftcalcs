import json
from pathlib import Path


def test_itemization_schema_fields_present():
    schema_path = Path(__file__).resolve().parent.parent / "config_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    props = schema["properties"]

    assert "available_components" in props
    assert "available_completed_items" in props
    assert "target_carries" in props
    assert "allow_reforge" in props
