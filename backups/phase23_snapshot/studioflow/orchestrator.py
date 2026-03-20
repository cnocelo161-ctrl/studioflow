import json

from models import OrchestratorRequest, OrchestratorResponse
from models import Phase1IntakeInput, ProgramInput, FieldReportInput, ScheduleInput
from proposal import generate_proposal
from program import generate_program
from field_report import generate_field_report
from schedule import compile_schedule

ACTION_MAP = {
    "generate_proposal":    (Phase1IntakeInput,  generate_proposal),
    "generate_program":     (ProgramInput,       generate_program),
    "generate_field_report":(FieldReportInput,   generate_field_report),
    "compile_schedule":     (ScheduleInput,      compile_schedule),
}


def run(request: OrchestratorRequest) -> OrchestratorResponse:
    input_model_cls, handler = ACTION_MAP[request.action]
    validated_input = input_model_cls(**request.payload)
    result = handler(validated_input)
    return OrchestratorResponse(action=request.action, result=result)


# SAMPLE REQUESTS — local CLI use only, not real workflow data
SAMPLE_REQUESTS = [
    {
        "action": "generate_proposal",
        "payload": {
            "client_name": "[SAMPLE CLIENT]",
            "property_address": "[SAMPLE ADDRESS]",
            "map": "00",
            "lot": "00",
            "project_type": "[SAMPLE PROJECT TYPE]",
            "scope_phases": ["pre_design", "SD", "DD"],
            "billing_mode": "hybrid",
            "probable_cost": 500000,
        },
    },
    {
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
    },
    {
        "action": "generate_field_report",
        "payload": {
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
    },
    {
        "action": "compile_schedule",
        "payload": {
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
    },
]

if __name__ == "__main__":
    for sample in SAMPLE_REQUESTS:
        request = OrchestratorRequest(**sample)
        response = run(request)
        print(json.dumps(response.model_dump(), indent=2))
        print()
