import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from models import FinishEntry, FixtureEntry, ScheduleInput, ScheduleOutput

# Source provenance constants — documentation only, not used in logic
SOURCE_PRIMARY = "Proposal for Services 2025 PDF"
SOURCE_SECONDARY = [
    "Client Planning Timeline PDF",
    "Program of Spaces template PDF",
    "Field Report template PDF",
]

# Source-grounded schedule categories (Proposal for Services §1.4 CD task 6):
#   Finish categories:  flooring | tile | paint_colors
#   Fixture types:      electrical | plumbing | cabinet | hardware | appliance
#
# Provisional FixtureEntry row fields (not source-confirmed):
#   manufacturer | model_number | finish_color | locations | quantity | notes


def compile_schedule(schedule_input: ScheduleInput) -> ScheduleOutput:
    schedule_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    # Group finish entries by level — insertion order preserved within each level
    finish_grouped: dict[str, list[FinishEntry]] = defaultdict(list)
    for entry in schedule_input.finish_entries:
        finish_grouped[entry.level].append(entry)
    finish_by_level = dict(finish_grouped)

    # Group fixture entries by type — insertion order preserved within each type
    fixture_grouped: dict[str, list[FixtureEntry]] = defaultdict(list)
    for entry in schedule_input.fixture_entries:
        fixture_grouped[entry.fixture_type].append(entry)
    fixtures_by_type = dict(fixture_grouped)

    # total_fixture_count: sum of all quantities; 0 when fixture_entries is empty
    total_fixture_count = sum(f.quantity for f in schedule_input.fixture_entries)

    return ScheduleOutput(
        schedule_id=schedule_id,
        project_id=schedule_input.project_id,
        finish_by_level=finish_by_level,
        fixtures_by_type=fixtures_by_type,
        total_fixture_count=total_fixture_count,
        document_ready=True,
        generated_at=generated_at,
    )


# SAMPLE INPUT — local CLI use only, not real workflow data
SAMPLE_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "finish_entries": [
        {
            "space_name": "Living Room",
            "level": "First Floor",
            "flooring": '3/4" White Oak, site-finished',
            "tile": None,
            "paint_colors": "BM OC-17 White Dove walls, OC-65 Chantilly Lace ceiling",
            "notes": None,
        },
        {
            "space_name": "Kitchen",
            "level": "First Floor",
            "flooring": '3/4" White Oak, site-finished',
            "tile": "Ann Sacks 3x6 white subway, running bond — backsplash",
            "paint_colors": "BM OC-17 White Dove",
            "notes": None,
        },
        {
            "space_name": "Primary Bath",
            "level": "Second Floor",
            "flooring": None,
            "tile": "Carrara marble 2x2 mosaic floor, 4x12 wall field",
            "paint_colors": "BM OC-65 Chantilly Lace",
            "notes": "Heated floor — coordinate with MEP",
        },
    ],
    "fixture_entries": [
        {
            "fixture_id": "E-01",
            "fixture_type": "electrical",
            "description": "Recessed downlight",
            "manufacturer": "Lightolier",
            "model_number": "LDR4",
            "finish_color": "White",
            "locations": ["Living Room", "Kitchen"],
            "quantity": 12,
            "notes": None,
        },
        {
            "fixture_id": "E-02",
            "fixture_type": "electrical",
            "description": "Pendant over kitchen island",
            "manufacturer": "Visual Comfort",
            "model_number": "TOB5228",
            "finish_color": "Aged Iron",
            "locations": ["Kitchen"],
            "quantity": 2,
            "notes": None,
        },
        {
            "fixture_id": "P-01",
            "fixture_type": "plumbing",
            "description": "Freestanding soaking tub",
            "manufacturer": "Waterworks",
            "model_number": "ETOILE",
            "finish_color": "White",
            "locations": ["Primary Bath"],
            "quantity": 1,
            "notes": None,
        },
        {
            "fixture_id": "H-01",
            "fixture_type": "hardware",
            "description": "Passage lever set",
            "manufacturer": "Rocky Mountain Hardware",
            "model_number": "E102",
            "finish_color": "Oil-Rubbed Bronze",
            "locations": [],
            "quantity": 4,
            "notes": "Quantity TBD pending final door count",
        },
    ],
    "additional_notes": ["Coordinate heated floor with MEP engineer prior to CD issue."],
}

if __name__ == "__main__":
    schedule_input = ScheduleInput(**SAMPLE_INPUT)
    output = compile_schedule(schedule_input)
    print(json.dumps(output.model_dump(), indent=2))
