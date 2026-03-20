import json
from pathlib import Path

from interface import app
from models import Phase1IntakeInput, ProgramInput, FieldReportInput, ScheduleInput
from proposal import generate_proposal
from program import generate_program
from field_report import generate_field_report
from schedule import compile_schedule

# ── Fixture loading — paths resolved relative to this file, not cwd ────────────

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

contract_proposal     = json.loads((FIXTURES_DIR / "contract_proposal.json").read_text())
contract_program      = json.loads((FIXTURES_DIR / "contract_program.json").read_text())
contract_field_report = json.loads((FIXTURES_DIR / "contract_field_report.json").read_text())
contract_schedule     = json.loads((FIXTURES_DIR / "contract_schedule.json").read_text())
contract_orchestrate  = json.loads((FIXTURES_DIR / "contract_orchestrate.json").read_text())
contract_workflow     = json.loads((FIXTURES_DIR / "contract_workflow.json").read_text())

# ── Strip helper — removes non-deterministic fields before comparison ──────────

NON_DETERMINISTIC = {"proposal_id", "project_id", "program_id",
                     "report_id", "schedule_id", "generated_at"}

def strip(d):
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in NON_DETERMINISTIC}
    if isinstance(d, list):
        return [strip(i) for i in d]
    return d

# ── Shared test payloads ───────────────────────────────────────────────────────

PROPOSAL_PAYLOAD = {
    "client_name": "[TEST CLIENT]", "property_address": "[TEST ADDRESS]",
    "map": "00", "lot": "00", "project_type": "[TEST TYPE]",
    "scope_phases": ["pre_design", "SD", "DD"], "billing_mode": "hybrid", "probable_cost": 500000,
}
PROGRAM_PAYLOAD = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "spaces": [{"name": "Living Room", "level": "First Floor", "width_ft": 18.0,
                "length_ft": 22.0, "sf": 396.0, "requirements": [], "adjacencies": []}],
}
FIELD_REPORT_PAYLOAD = {
    "project_id": "00000000-0000-0000-0000-000000000002",
    "visit_date": "2026-03-18", "visit_time": "10:00 AM", "weather": "Clear",
    "approximate_temp_f": 52.0, "phase": "Construction Administration",
    "work_in_progress": "Framing", "parties_present": ["General Contractor"],
    "transmitted_to": ["Client"], "observations": ["Framing on track per drawings"],
    "action_required": [], "old_items": [],
    "new_items": [{"item_number": "001", "description": "Verify header size at main entry",
                   "responsible_party": "General Contractor", "status": "open"}],
    "site_photos": [],
}
SCHEDULE_PAYLOAD = {
    "project_id": "00000000-0000-0000-0000-000000000003",
    "finish_entries": [{"space_name": "Living Room", "level": "First Floor",
                        "flooring": "White Oak Hardwood", "tile": None,
                        "paint_colors": "BM White Dove OC-17"}],
    "fixture_entries": [],
}

client = app.test_client()

# ── Section A: Direct module contract tests ────────────────────────────────────

proposal = generate_proposal(Phase1IntakeInput(**PROPOSAL_PAYLOAD))
assert strip(proposal.model_dump()) == contract_proposal
assert proposal.proposal_id
assert proposal.project_id
assert "+00:00" in proposal.generated_at or "Z" in proposal.generated_at
print("Section A: generate_proposal contract passed.")

program = generate_program(ProgramInput(**PROGRAM_PAYLOAD))
assert strip(program.model_dump()) == contract_program
assert program.program_id
assert "+00:00" in program.generated_at or "Z" in program.generated_at
print("Section A: generate_program contract passed.")

report = generate_field_report(FieldReportInput(**FIELD_REPORT_PAYLOAD))
assert strip(report.model_dump()) == contract_field_report
assert report.report_id
assert "+00:00" in report.generated_at or "Z" in report.generated_at
print("Section A: generate_field_report contract passed.")

schedule = compile_schedule(ScheduleInput(**SCHEDULE_PAYLOAD))
assert strip(schedule.model_dump()) == contract_schedule
assert schedule.schedule_id
assert "+00:00" in schedule.generated_at or "Z" in schedule.generated_at
print("Section A: compile_schedule contract passed.")

# ── Section B: /orchestrate contract tests ─────────────────────────────────────

ORCHESTRATE_PAYLOADS = {
    "generate_proposal":    PROPOSAL_PAYLOAD,
    "generate_program":     PROGRAM_PAYLOAD,
    "generate_field_report": FIELD_REPORT_PAYLOAD,
    "compile_schedule":     SCHEDULE_PAYLOAD,
}

for action, payload in ORCHESTRATE_PAYLOADS.items():
    r = client.post("/orchestrate", json={"action": action, "payload": payload})
    assert r.status_code == 200
    data = r.get_json()
    assert data["action"] == action
    assert strip(data["result"]) == contract_orchestrate[action]

print("Section B: /orchestrate all 4 routes contract passed.")

# ── Section C: /workflow contract test ─────────────────────────────────────────

r = client.post("/workflow", json={
    "proposal_intake": PROPOSAL_PAYLOAD,
    "program_payload": {k: v for k, v in PROGRAM_PAYLOAD.items() if k != "project_id"},
    "field_report_payload": {k: v for k, v in FIELD_REPORT_PAYLOAD.items() if k != "project_id"},
    "schedule_payload": {k: v for k, v in SCHEDULE_PAYLOAD.items() if k != "project_id"},
})
assert r.status_code == 200
data = r.get_json()

# project_id consistency — relative assertion
assert data["project_id"]
assert data["proposal"]["project_id"]     == data["project_id"]
assert data["program"]["project_id"]      == data["project_id"]
assert data["field_report"]["project_id"] == data["project_id"]
assert data["schedule"]["project_id"]     == data["project_id"]

# workflow-level timestamp — loose
assert "+00:00" in data["generated_at"] or "Z" in data["generated_at"]

# fixture comparison — strict
assert strip(data) == contract_workflow

print("Section C: /workflow contract passed.")

# ── Section D: Error contract tests ───────────────────────────────────────────

r = client.post("/orchestrate", json={"action": "bad_action", "payload": {}})
assert r.status_code == 422
err = r.get_json()
assert err["error"] == "validation_error"
assert err["detail"]

r = client.post("/orchestrate", json={"action": "generate_proposal", "payload": {}})
assert r.status_code == 422
assert r.get_json()["error"] == "validation_error"

r = client.post("/workflow", json={
    "proposal_intake": PROPOSAL_PAYLOAD,
    "program_payload": {},
    "field_report_payload": {},
    "schedule_payload": {},
})
assert r.status_code == 422
assert r.get_json()["error"] == "validation_error"

print("Section D: error contracts passed.")
print("All Phase 8 regression tests passed.")
