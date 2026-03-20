from models import ProgramInput, ProgramSpace
from program import generate_program

# TEST INPUT — not real workflow data. Structurally valid minimal fixture only.
TEST_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "spaces": [
        {
            "name": "Entry Hall",
            "level": "First Floor",
            "width_ft": 8.0,
            "length_ft": 12.0,
            "sf": 96.0,
            "requirements": ["Coat storage"],
            "adjacencies": ["Living Room"],
        },
        {
            "name": "Living Room",
            "level": "First Floor",
            "width_ft": 18.0,
            "length_ft": 22.0,
            "sf": 396.0,
            "requirements": ["Fireplace"],
            "adjacencies": ["Entry Hall"],
        },
        {
            "name": "Primary Bedroom",
            "level": "Second Floor",
            "width_ft": 16.0,
            "length_ft": 20.0,
            "sf": 320.0,
            "requirements": ["En-suite bath"],
            "adjacencies": ["Upper Hall"],
        },
    ],
    "design_intent": "Open-plan first floor with private bedroom suite above.",
}
# net_sf = 96 + 396 + 320 = 812.0
# gross_sf = 812.0 * 1.10 = 893.2

program_input = ProgramInput(**TEST_INPUT)
output = generate_program(program_input)

assert output.net_sf == 812.0
assert output.gross_sf == 893.2
assert output.circulation_factor == 0.10
assert output.document_ready is True
assert output.program_id  # valid non-empty string
assert "+00:00" in output.generated_at or "Z" in output.generated_at
assert output.project_id == "00000000-0000-0000-0000-000000000001"

# grouping
assert "First Floor" in output.spaces_by_level
assert "Second Floor" in output.spaces_by_level
assert len(output.spaces_by_level["First Floor"]) == 2
assert len(output.spaces_by_level["Second Floor"]) == 1
assert output.spaces_by_level["First Floor"][0].name == "Entry Hall"
assert output.spaces_by_level["Second Floor"][0].name == "Primary Bedroom"

print("All Phase 2 assertions passed.")
