import json
from datetime import datetime, timezone

from models import (
    FieldReportInput,
    ProgramInput,
    ScheduleInput,
    WorkflowInput,
    WorkflowOutput,
)
from proposal import generate_proposal
from program import generate_program
from field_report import generate_field_report
from schedule import compile_schedule


def run_workflow(workflow_input: WorkflowInput) -> WorkflowOutput:
    generated_at = datetime.now(timezone.utc).isoformat()

    proposal = generate_proposal(workflow_input.proposal_intake)
    project_id = proposal.project_id

    program = generate_program(
        ProgramInput(project_id=project_id, **workflow_input.program_payload)
    )
    field_report = generate_field_report(
        FieldReportInput(project_id=project_id, **workflow_input.field_report_payload)
    )
    schedule = compile_schedule(
        ScheduleInput(project_id=project_id, **workflow_input.schedule_payload)
    )

    return WorkflowOutput(
        project_id=project_id,
        proposal=proposal,
        program=program,
        field_report=field_report,
        schedule=schedule,
        generated_at=generated_at,
    )


# SAMPLE WORKFLOW INPUT — local CLI use only, not real workflow data
SAMPLE_WORKFLOW_INPUT = WorkflowInput(
    proposal_intake={
        "client_name": "[SAMPLE CLIENT]",
        "property_address": "[SAMPLE ADDRESS]",
        "map": "00",
        "lot": "00",
        "project_type": "[SAMPLE PROJECT TYPE]",
        "scope_phases": ["pre_design", "SD", "DD"],
        "billing_mode": "hybrid",
        "probable_cost": 500000,
    },
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
)

if __name__ == "__main__":
    result = run_workflow(SAMPLE_WORKFLOW_INPUT)
    print(json.dumps(result.model_dump(), indent=2))
