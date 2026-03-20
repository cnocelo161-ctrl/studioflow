import json
import uuid
from datetime import datetime, timezone

from models import FieldReportInput, FieldReportOutput

# Source provenance constants — documentation only, not used in logic
SOURCE_PRIMARY = "Field Report template PDF"
SOURCE_SECONDARY = [
    "Proposal for Services 2025 PDF",
    "Client Planning Timeline PDF",
    "Program of Spaces template PDF",
]


def generate_field_report(report_input: FieldReportInput) -> FieldReportOutput:
    report_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    # open_item_count: status "open" or "in_progress" counted; only "closed" excluded
    # insertion order of old_items and new_items is preserved from input; no sorting applied
    # result is 0 when both lists are empty
    open_item_count = sum(
        1
        for item in report_input.old_items + report_input.new_items
        if item.status != "closed"
    )

    return FieldReportOutput(
        report_id=report_id,
        project_id=report_input.project_id,
        visit_date=report_input.visit_date,
        visit_time=report_input.visit_time,
        weather=report_input.weather,
        approximate_temp_f=report_input.approximate_temp_f,
        phase=report_input.phase,
        work_in_progress=report_input.work_in_progress,
        parties_present=report_input.parties_present,
        transmitted_to=report_input.transmitted_to,
        observations=report_input.observations,
        action_required=report_input.action_required,
        old_items=report_input.old_items,
        new_items=report_input.new_items,
        open_item_count=open_item_count,
        site_photos=report_input.site_photos,
        document_ready=True,
        generated_at=generated_at,
    )


# SAMPLE INPUT — local CLI use only, not real workflow data
SAMPLE_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "visit_date": "2026-03-18",
    "visit_time": "10:30",
    "weather": "Partly cloudy",
    "approximate_temp_f": 52.0,
    "phase": "Construction Administration",
    "work_in_progress": "Framing of second floor exterior walls underway. Subfloor complete on first floor.",
    "parties_present": ["J. Sherman, Architect", "T. Brady, General Contractor"],
    "transmitted_to": ["Client"],
    "observations": [
        "Exterior framing at northeast corner does not match approved drawings — gap in sheathing at sill plate.",
        "First floor subfloor is complete and dimensionally consistent with construction documents.",
    ],
    "action_required": [
        "Contractor to review and correct northeast corner framing before next site visit.",
    ],
    "old_items": [
        {
            "item_number": "001",
            "description": "Footing depth discrepancy at south wall — resolved per structural engineer directive.",
            "responsible_party": "General Contractor",
            "status": "closed",
        },
    ],
    "new_items": [
        {
            "item_number": "002",
            "description": "Sheathing gap at northeast corner sill plate.",
            "responsible_party": "General Contractor",
            "status": "open",
        },
        {
            "item_number": "003",
            "description": "Confirm window rough opening dimensions against Door and Window Schedule.",
            "responsible_party": None,
            "status": "in_progress",
        },
    ],
    "site_photos": ["FR-2026-03-18-001.jpg", "FR-2026-03-18-002.jpg"],
}

if __name__ == "__main__":
    report_input = FieldReportInput(**SAMPLE_INPUT)
    report = generate_field_report(report_input)
    print(json.dumps(report.model_dump(), indent=2))
