from pydantic import ValidationError

from models import FinishEntry, FixtureEntry, ScheduleInput
from schedule import compile_schedule

# TEST INPUT — not real workflow data. Structurally valid minimal fixture only.
TEST_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "finish_entries": [
        {
            "space_name": "Living Room",
            "level": "First Floor",
            "flooring": '3/4" White Oak, site-finished',
            "tile": None,
            "paint_colors": "BM OC-17 White Dove",
            "notes": None,
        },
        {
            "space_name": "Kitchen",
            "level": "First Floor",
            "flooring": '3/4" White Oak, site-finished',
            "tile": "3x6 white subway tile",
            "paint_colors": "BM OC-17 White Dove",
            "notes": None,
        },
        {
            "space_name": "Primary Bath",
            "level": "Second Floor",
            "flooring": None,
            "tile": "Carrara marble 2x2 mosaic",
            "paint_colors": "BM OC-65 Chantilly Lace",
            "notes": "Heated floor",
        },
    ],
    "fixture_entries": [
        {
            "fixture_id": "E-01",
            "fixture_type": "electrical",
            "description": "Recessed downlight",
            "quantity": 4,            # provisional field — tests total_fixture_count
            "locations": ["Living Room", "Kitchen"],
        },
        {
            "fixture_id": "E-02",
            "fixture_type": "electrical",
            "description": "Pendant over kitchen island",
            "quantity": 2,
            "locations": ["Kitchen"],
        },
        {
            "fixture_id": "P-01",
            "fixture_type": "plumbing",
            "description": "Freestanding soaking tub",
            "quantity": 1,
            "locations": ["Primary Bath"],
        },
        {
            "fixture_id": "H-01",
            "fixture_type": "hardware",
            "description": "Passage lever set",
            "quantity": 3,
            "locations": [],           # provisional field — tests empty locations is valid
        },
    ],
    "additional_notes": ["Test schedule — not real workflow data."],
}
# total_fixture_count: 4 + 2 + 1 + 3 = 10

schedule_input = ScheduleInput(**TEST_INPUT)
output = compile_schedule(schedule_input)

assert output.document_ready is True
assert output.schedule_id  # valid non-empty string
assert "+00:00" in output.generated_at or "Z" in output.generated_at
assert output.project_id == "00000000-0000-0000-0000-000000000001"

# finish grouping by level
assert "First Floor" in output.finish_by_level
assert "Second Floor" in output.finish_by_level
assert len(output.finish_by_level["First Floor"]) == 2
assert len(output.finish_by_level["Second Floor"]) == 1

# insertion order preserved
assert output.finish_by_level["First Floor"][0].space_name == "Living Room"
assert output.finish_by_level["First Floor"][1].space_name == "Kitchen"

# fixture grouping by type
assert "electrical" in output.fixtures_by_type
assert "plumbing" in output.fixtures_by_type
assert "hardware" in output.fixtures_by_type
assert len(output.fixtures_by_type["electrical"]) == 2
assert len(output.fixtures_by_type["plumbing"]) == 1
assert len(output.fixtures_by_type["hardware"]) == 1

# total_fixture_count: 4 + 2 + 1 + 3 = 10
assert output.total_fixture_count == 10

# source-grounded finish fields preserved
assert output.finish_by_level["First Floor"][0].flooring == '3/4" White Oak, site-finished'
assert output.finish_by_level["Second Floor"][0].tile == "Carrara marble 2x2 mosaic"

# provisional field: empty locations is valid
assert output.fixtures_by_type["hardware"][0].locations == []

print("All passing assertions passed.")

# FAILING CASE 1: empty finish_entries must raise ValidationError
bad_input_1 = {**TEST_INPUT, "finish_entries": []}

try:
    ScheduleInput(**bad_input_1)
    raise AssertionError("Expected ValidationError was not raised for empty finish_entries")
except ValidationError:
    pass  # correct — validation rejected invalid input

print("Failing case 1 passed (empty finish_entries → ValidationError).")

# FAILING CASE 2: FixtureEntry with quantity=0 must raise ValidationError
try:
    FixtureEntry(
        fixture_id="X-01",
        fixture_type="electrical",
        description="Test fixture",
        quantity=0,
    )
    raise AssertionError("Expected ValidationError was not raised for quantity=0")
except ValidationError:
    pass  # correct — validation rejected invalid input

print("Failing case 2 passed (quantity=0 → ValidationError).")
print("All tests passed.")
