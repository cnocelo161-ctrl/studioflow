from interface import app

client = app.test_client()

# ── /orchestrate passing — generate_proposal ───────────────────────────────────

response = client.post("/orchestrate", json={
    "action": "generate_proposal",
    "payload": {
        "client_name": "[TEST CLIENT]",
        "property_address": "[TEST ADDRESS]",
        "map": "00",
        "lot": "00",
        "project_type": "[TEST TYPE]",
        "scope_phases": ["pre_design", "SD", "DD"],
        "billing_mode": "hybrid",
        "probable_cost": 500000,
    },
})
assert response.status_code == 200
data = response.get_json()
assert data["action"] == "generate_proposal"
assert data["result"]["proposal_id"]
assert data["result"]["generated_at"]

print("/orchestrate generate_proposal passed.")

# ── /orchestrate passing — generate_program ────────────────────────────────────

response = client.post("/orchestrate", json={
    "action": "generate_program",
    "payload": {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "spaces": [
            {
                "name": "Living Room",
                "level": "First Floor",
                "width_ft": 18.0,
                "length_ft": 22.0,
                "sf": 396.0,
                "requirements": [],
                "adjacencies": [],
            }
        ],
    },
})
assert response.status_code == 200
data = response.get_json()
assert data["action"] == "generate_program"
assert data["result"]["net_sf"] == 396.0

print("/orchestrate generate_program passed.")

# ── /workflow passing — full E2E ───────────────────────────────────────────────

response = client.post("/workflow", json={
    "proposal_intake": {
        "client_name": "[TEST CLIENT]",
        "property_address": "[TEST ADDRESS]",
        "map": "00",
        "lot": "00",
        "project_type": "[TEST TYPE]",
        "scope_phases": ["pre_design", "SD", "DD"],
        "billing_mode": "hybrid",
        "probable_cost": 500000,
    },
    "program_payload": {
        "spaces": [
            {
                "name": "Living Room",
                "level": "First Floor",
                "width_ft": 18.0,
                "length_ft": 22.0,
                "sf": 396.0,
                "requirements": [],
                "adjacencies": [],
            }
        ]
    },
    "field_report_payload": {
        "visit_date": "2026-03-18",
        "visit_time": "10:00 AM",
        "weather": "Clear",
        "approximate_temp_f": 52.0,
        "phase": "Construction Administration",
        "work_in_progress": "Framing",
        "parties_present": ["General Contractor"],
        "transmitted_to": ["Client"],
        "observations": ["Framing on track per drawings"],
        "action_required": [],
        "old_items": [],
        "new_items": [
            {
                "item_number": "001",
                "description": "Verify header size at main entry",
                "responsible_party": "General Contractor",
                "status": "open",
            }
        ],
        "site_photos": [],
    },
    "schedule_payload": {
        "finish_entries": [
            {
                "space_name": "Living Room",
                "level": "First Floor",
                "flooring": "White Oak Hardwood",
                "tile": None,
                "paint_colors": "BM White Dove OC-17",
            }
        ],
        "fixture_entries": [],
    },
})
assert response.status_code == 200
data = response.get_json()
assert data["project_id"]
assert data["proposal"]["project_id"]    == data["project_id"]
assert data["program"]["project_id"]     == data["project_id"]
assert data["field_report"]["project_id"] == data["project_id"]
assert data["schedule"]["project_id"]    == data["project_id"]

print("/workflow full E2E passed.")

# ── /orchestrate failing — invalid action → 422 ────────────────────────────────

response = client.post("/orchestrate", json={"action": "unknown_action", "payload": {}})
assert response.status_code == 422
assert response.get_json()["error"] == "validation_error"

print("/orchestrate invalid action → 422 passed.")

# ── /orchestrate failing — valid action, empty payload → 422 ──────────────────

response = client.post("/orchestrate", json={"action": "generate_proposal", "payload": {}})
assert response.status_code == 422
assert response.get_json()["error"] == "validation_error"

print("/orchestrate empty payload → 422 passed.")

# ── /workflow failing — missing program spaces → 422 ──────────────────────────

response = client.post("/workflow", json={
    "proposal_intake": {
        "client_name": "[TEST CLIENT]",
        "property_address": "[TEST ADDRESS]",
        "map": "00",
        "lot": "00",
        "project_type": "[TEST TYPE]",
        "scope_phases": ["pre_design"],
        "billing_mode": "hourly",
    },
    "program_payload": {},
    "field_report_payload": {},
    "schedule_payload": {},
})
assert response.status_code == 422
assert response.get_json()["error"] == "validation_error"

print("/workflow missing program spaces → 422 passed.")

print("All Phase 7 tests passed.")
