from pydantic import ValidationError

from models import Phase1IntakeInput, WorkflowInput
from workflow import run_workflow

# ── Passing test — full E2E chain ──────────────────────────────────────────────

result = run_workflow(WorkflowInput(
    proposal_intake=Phase1IntakeInput(
        client_name="[TEST CLIENT]",
        property_address="[TEST ADDRESS]",
        map="00",
        lot="00",
        project_type="[TEST TYPE]",
        scope_phases=["pre_design", "SD", "DD"],
        billing_mode="hybrid",
        probable_cost=500000,
    ),
    program_payload={
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
    field_report_payload={
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
    schedule_payload={
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

# Project identity — all outputs share the same project_id
assert result.project_id
assert result.proposal.project_id    == result.project_id
assert result.program.project_id     == result.project_id
assert result.field_report.project_id == result.project_id
assert result.schedule.project_id    == result.project_id

# Phase outputs
assert result.proposal.document_ready is True
assert result.proposal.scope_of_services
assert result.program.net_sf == 396.0
assert result.field_report.open_item_count == 1
assert "First Floor" in result.schedule.finish_by_level

# Workflow-level timestamp
assert result.generated_at
assert "+00:00" in result.generated_at or "Z" in result.generated_at

print("Passing test (full E2E chain) passed.")

# ── Failing test — invalid program_payload raises ValidationError at run time ──

try:
    run_workflow(WorkflowInput(
        proposal_intake=Phase1IntakeInput(
            client_name="[TEST CLIENT]",
            property_address="[TEST ADDRESS]",
            map="00",
            lot="00",
            project_type="[TEST TYPE]",
            scope_phases=["pre_design"],
            billing_mode="hourly",
        ),
        program_payload={},   # missing required 'spaces' field
        field_report_payload={},
        schedule_payload={},
    ))
    raise AssertionError("Expected ValidationError was not raised")
except ValidationError:
    pass

print("Failing test (invalid program_payload) passed.")
print("All Phase 6 tests passed.")
