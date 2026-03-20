import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from interface import app

client = app.test_client()

VALID_PROGRAM_PAYLOAD = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "spaces": [{"name": "Living Room", "level": "First Floor", "width_ft": 18.0,
                "length_ft": 22.0, "sf": 396.0, "requirements": [], "adjacencies": []}],
}
VALID_PROPOSAL_INTAKE = {
    "client_name": "[TEST CLIENT]", "property_address": "[TEST ADDRESS]",
    "map": "00", "lot": "00", "project_type": "[TEST TYPE]",
    "scope_phases": ["pre_design"], "billing_mode": "hourly",
}


def read_records(path):
    return [json.loads(line) for line in Path(path).read_text().strip().splitlines()]


with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
    tmp_path = Path(tmp.name)

with patch("logger.LOG_PATH", tmp_path):

    # ── Case 1: Success /orchestrate ──────────────────────────────────────────

    client.post("/orchestrate", json={"action": "generate_program", "payload": VALID_PROGRAM_PAYLOAD})
    records = read_records(tmp_path)
    assert len(records) == 1
    r = records[0]
    assert r["route"] == "/orchestrate"
    assert r["action"] == "generate_program"
    assert r["outcome"] == "success"
    assert r["status"] == 200
    assert r["error_type"] is None
    assert r["duration_ms"] >= 0
    assert "+00:00" in r["timestamp"] or "Z" in r["timestamp"]
    assert "payload" not in r
    assert "client_name" not in r

    print("Case 1: success /orchestrate logged correctly.")

    # ── Case 2: Validation error ───────────────────────────────────────────────

    client.post("/orchestrate", json={"action": "bad_action", "payload": {}})
    records = read_records(tmp_path)
    assert len(records) == 2
    r = records[1]
    assert r["route"] == "/orchestrate"
    assert r["action"] == "bad_action"
    assert r["outcome"] == "error"
    assert r["status"] == 422
    assert r["error_type"] == "validation_error"

    print("Case 2: validation error logged correctly.")

    # ── Case 3: Forced internal error → 500 ───────────────────────────────────

    with patch("interface.run", side_effect=RuntimeError("forced")):
        client.post("/orchestrate", json={"action": "generate_program", "payload": VALID_PROGRAM_PAYLOAD})
    records = read_records(tmp_path)
    assert len(records) == 3
    r = records[2]
    assert r["outcome"] == "error"
    assert r["status"] == 500
    assert r["error_type"] == "internal_error"
    assert "forced" not in json.dumps(r)  # error message not leaked into log

    print("Case 3: forced 500 logged correctly.")

    # ── Case 4: Workflow success ───────────────────────────────────────────────

    client.post("/workflow", json={
        "proposal_intake": VALID_PROPOSAL_INTAKE,
        "program_payload": {
            "spaces": [{"name": "Living Room", "level": "First Floor", "width_ft": 18.0,
                        "length_ft": 22.0, "sf": 396.0, "requirements": [], "adjacencies": []}],
        },
        "field_report_payload": {
            "visit_date": "2026-03-19", "visit_time": "10:00 AM", "weather": "Clear",
            "approximate_temp_f": 52.0, "phase": "CA", "work_in_progress": "Framing",
            "parties_present": ["GC"], "transmitted_to": ["Client"],
            "observations": ["On track"], "action_required": [],
            "old_items": [], "new_items": [], "site_photos": [],
        },
        "schedule_payload": {
            "finish_entries": [{"space_name": "Living Room", "level": "First Floor",
                                "flooring": "Oak", "tile": None, "paint_colors": "White"}],
            "fixture_entries": [],
        },
    })
    records = read_records(tmp_path)
    assert len(records) == 4
    r = records[3]
    assert r["route"] == "/workflow"
    assert r["action"] == "workflow"
    assert r["outcome"] == "success"
    assert r["status"] == 200
    assert r["error_type"] is None

    print("Case 4: workflow success logged correctly.")

    # ── Case 5: Multiple requests append, not overwrite ───────────────────────

    assert len(records) == 4

    print("Case 5: multiple requests append to log.")

    # ── Case 6: Malformed body — action is null ───────────────────────────────

    client.post("/orchestrate", data="not-json", content_type="text/plain")
    records = read_records(tmp_path)
    assert len(records) == 5
    r = records[4]
    assert r["action"] is None
    assert r["outcome"] == "error"
    assert r["status"] == 422

    print("Case 6: malformed body — action null logged correctly.")

tmp_path.unlink(missing_ok=True)
print("All Phase 10 tests passed.")
