import json
from models import ProjectIntakeInput, NormalizedIntake
from pydantic import ValidationError


def handle_project_intake(raw: dict) -> dict:
    """
    Accepts a raw project intake dict, validates and normalizes it.
    Returns a dict with normalized fields or a validation error.
    """
    try:
        intake = ProjectIntakeInput(**raw)
    except ValidationError as e:
        details = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in e.errors()
        ]
        return {
            "status": "error",
            "error": "invalid_input",
            "details": details,
        }

    normalized = intake.normalize()

    return {
        "status": "ok",
        "action": intake.action,
        "normalized": normalized.model_dump(),
    }


if __name__ == "__main__":
    sample = {
        "action": "project_intake",
        "client_name": "Sarah Chen",
        "project_type": "Residential Addition",
        "location": "Denver, CO",
        "description": "3-bedroom home addition, approximately 1200 sq ft, modern design with sustainable materials.",
        "budget": "$450,000",
        "timeline": "18 months",
    }

    result = handle_project_intake(sample)
    print(json.dumps(result, indent=2))

    print("\n--- Missing optional fields ---")
    sparse = {
        "action": "project_intake",
        "client_name": "",
        "project_type": "Commercial Renovation",
        "location": "",
        "description": "Office lobby redesign",
        "budget": "",
        "timeline": "",
    }
    print(json.dumps(handle_project_intake(sparse), indent=2))

    print("\n--- Wrong action ---")
    bad = {**sample, "action": "wrong_action"}
    print(json.dumps(handle_project_intake(bad), indent=2))
