from pydantic import ValidationError

from models import OrchestratorRequest
from orchestrator import run

# ── Route 1: generate_proposal ─────────────────────────────────────────────────

response = run(OrchestratorRequest(
    action="generate_proposal",
    payload={
        "client_name": "[TEST CLIENT]",
        "property_address": "[TEST ADDRESS]",
        "map": "00",
        "lot": "00",
        "project_type": "[TEST TYPE]",
        "scope_phases": ["pre_design", "SD", "DD"],
        "billing_mode": "hybrid",
        "probable_cost": 500000,
    },
))
assert response.action == "generate_proposal"
assert response.result.proposal_id
assert response.result.scope_of_services
assert response.result.generated_at

print("Route 1 (generate_proposal) passed.")

# ── Route 2: generate_program ──────────────────────────────────────────────────

response = run(OrchestratorRequest(
    action="generate_program",
    payload={
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
))
assert response.action == "generate_program"
assert response.result.net_sf == 396.0

print("Route 2 (generate_program) passed.")

# ── Route 3: generate_field_report ────────────────────────────────────────────

response = run(OrchestratorRequest(
    action="generate_field_report",
    payload={
        "project_id": "00000000-0000-0000-0000-000000000002",
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
))
assert response.action == "generate_field_report"
assert response.result.report_id
assert response.result.open_item_count == 1

print("Route 3 (generate_field_report) passed.")

# ── Route 4: compile_schedule ──────────────────────────────────────────────────

response = run(OrchestratorRequest(
    action="compile_schedule",
    payload={
        "project_id": "00000000-0000-0000-0000-000000000003",
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
))
assert response.action == "compile_schedule"
assert response.result.schedule_id
assert "First Floor" in response.result.finish_by_level

print("Route 4 (compile_schedule) passed.")

# ── Failing case 1: invalid action ────────────────────────────────────────────

try:
    OrchestratorRequest(action="unknown_action", payload={})
    raise AssertionError("Expected ValidationError was not raised")
except ValidationError:
    pass

print("Failing case 1 (invalid action) passed.")

# ── Failing case 2: valid action, invalid payload ──────────────────────────────

try:
    run(OrchestratorRequest(action="generate_proposal", payload={}))
    raise AssertionError("Expected ValidationError was not raised")
except ValidationError:
    pass

print("Failing case 2 (invalid payload) passed.")
print("All Phase 5 tests passed.")
