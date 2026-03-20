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

# ── Case 1: Invalid action → 422 ──────────────────────────────────────────────

r = client.post("/orchestrate", json={"action": "bad_action", "payload": {}})
assert r.status_code == 422
data = r.get_json()
assert data["error"] == "validation_error"
assert data["status"] == 422
assert data["detail"]
assert isinstance(data["errors"], list)
assert len(data["errors"]) >= 1
assert "loc" in data["errors"][0]
assert "msg" in data["errors"][0]
assert "type" in data["errors"][0]

print("Case 1: invalid action → 422 passed.")

# ── Case 2: Valid action, missing payload fields → 422 ────────────────────────

r = client.post("/orchestrate", json={"action": "generate_proposal", "payload": {}})
assert r.status_code == 422
data = r.get_json()
assert data["status"] == 422
assert isinstance(data["errors"], list)
assert len(data["errors"]) >= 1

print("Case 2: missing payload fields → 422 passed.")

# ── Case 3: Workflow invalid payload → 422 ────────────────────────────────────

r = client.post("/workflow", json={
    "proposal_intake": VALID_PROPOSAL_INTAKE,
    "program_payload": {},
    "field_report_payload": {},
    "schedule_payload": {},
})
assert r.status_code == 422
data = r.get_json()
assert data["status"] == 422
assert isinstance(data["errors"], list)

print("Case 3: workflow invalid payload → 422 passed.")

# ── Case 4: Success has no error fields → 200 ─────────────────────────────────

r = client.post("/orchestrate", json={"action": "generate_program", "payload": VALID_PROGRAM_PAYLOAD})
assert r.status_code == 200
data = r.get_json()
assert "errors" not in data
assert "status" not in data

print("Case 4: success has no error fields → 200 passed.")

# ── Case 5: Forced internal error → 500 ──────────────────────────────────────

with patch("interface.run", side_effect=Exception("forced internal error")):
    r = client.post("/orchestrate", json={"action": "generate_program", "payload": VALID_PROGRAM_PAYLOAD})
    assert r.status_code == 500
    data = r.get_json()
    assert data["error"] == "internal_error"
    assert data["status"] == 500
    assert data["detail"]
    assert "errors" not in data

print("Case 5: forced internal error → 500 passed.")
print("All Phase 9 tests passed.")
