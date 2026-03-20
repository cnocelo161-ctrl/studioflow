from pydantic import ValidationError

from models import FieldReportInput, FieldReportItem
from field_report import generate_field_report

# TEST INPUT — not real workflow data. Structurally valid minimal fixture only.
TEST_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "visit_date": "2026-03-18",
    "visit_time": "10:30",
    "weather": "Partly cloudy",
    "approximate_temp_f": 52.0,
    "phase": "Construction Administration",
    "work_in_progress": "Framing of second floor exterior walls underway.",
    "parties_present": ["J. Sherman, Architect", "T. Brady, General Contractor"],
    "transmitted_to": ["Client"],
    "observations": [
        "Northeast corner framing gap in sheathing at sill plate.",
        "First floor subfloor complete and dimensionally consistent.",
    ],
    "action_required": [
        "Contractor to correct northeast corner framing.",
    ],
    "old_items": [
        {
            "item_number": "001",
            "description": "Footing depth discrepancy at south wall — resolved.",
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
            "description": "Confirm window rough opening dimensions.",
            "responsible_party": None,   # tests Optional[str]
            "status": "in_progress",
        },
    ],
    "site_photos": ["FR-2026-03-18-001.jpg", "FR-2026-03-18-002.jpg"],
}
# open_item_count: old "001" closed=1, new "002" open + "003" in_progress → 2

report_input = FieldReportInput(**TEST_INPUT)
report = generate_field_report(report_input)

assert report.document_ready is True
assert report.report_id  # valid non-empty string
assert "+00:00" in report.generated_at or "Z" in report.generated_at
assert report.open_item_count == 2  # "open" + "in_progress" counted; "closed" excluded
assert report.visit_date == "2026-03-18"
assert len(report.parties_present) == 2
assert len(report.observations) == 2
assert len(report.old_items) == 1
assert len(report.new_items) == 2
assert len(report.site_photos) == 2
assert report.old_items[0].status == "closed"
assert report.new_items[0].status == "open"
assert report.new_items[1].responsible_party is None

print("All passing assertions passed.")

# FAILING CASE 1: empty parties_present must raise ValidationError
bad_input_1 = {**TEST_INPUT, "parties_present": []}

try:
    FieldReportInput(**bad_input_1)
    raise AssertionError("Expected ValidationError was not raised for empty parties_present")
except ValidationError:
    pass  # correct — validation rejected invalid input

print("Failing case 1 passed (empty parties_present → ValidationError).")

# FAILING CASE 2: FieldReportItem with empty item_number must raise ValidationError
try:
    FieldReportItem(
        item_number="",
        description="Some description",
        responsible_party=None,
        status="open",
    )
    raise AssertionError("Expected ValidationError was not raised for empty item_number")
except ValidationError:
    pass  # correct — validation rejected invalid input

print("Failing case 2 passed (item_number='' → ValidationError).")
print("All tests passed.")
