import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from models import ProgramInput, ProgramOutput, ProgramSpace


def generate_program(program_input: ProgramInput) -> ProgramOutput:
    program_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    net_sf = round(sum(space.sf for space in program_input.spaces), 2)
    circulation_factor = 0.10
    gross_sf = round(net_sf * (1 + circulation_factor), 2)

    grouped: dict[str, list[ProgramSpace]] = defaultdict(list)
    for space in program_input.spaces:
        grouped[space.level].append(space)
    spaces_by_level = dict(grouped)

    return ProgramOutput(
        program_id=program_id,
        project_id=program_input.project_id,
        net_sf=net_sf,
        circulation_factor=circulation_factor,
        gross_sf=gross_sf,
        spaces_by_level=spaces_by_level,
        document_ready=True,
        generated_at=generated_at,
    )


# SAMPLE INPUT — local CLI use only, not real workflow data
SAMPLE_INPUT = {
    "project_id": "00000000-0000-0000-0000-000000000001",
    "spaces": [
        {
            "name": "Entry Hall",
            "level": "First Floor",
            "width_ft": 8.0,
            "length_ft": 12.0,
            "sf": 96.0,
            "requirements": ["Coat storage", "Natural light"],
            "adjacencies": ["Living Room", "Kitchen"],
        },
        {
            "name": "Living Room",
            "level": "First Floor",
            "width_ft": 18.0,
            "length_ft": 22.0,
            "sf": 396.0,
            "requirements": ["Fireplace", "South-facing windows"],
            "adjacencies": ["Entry Hall", "Dining Room"],
        },
        {
            "name": "Primary Bedroom",
            "level": "Second Floor",
            "width_ft": 16.0,
            "length_ft": 20.0,
            "sf": 320.0,
            "requirements": ["En-suite bath", "Walk-in closet"],
            "adjacencies": ["Primary Bath", "Upper Hall"],
        },
    ],
    "design_intent": "Open-plan first floor with private bedroom suite above.",
    "additional_notes": ["Client prefers passive solar orientation"],
}

if __name__ == "__main__":
    program_input = ProgramInput(**SAMPLE_INPUT)
    output = generate_program(program_input)
    print(json.dumps(output.model_dump(), indent=2))
