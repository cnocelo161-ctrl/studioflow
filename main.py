import json
from studioflow.processor import generate_project_output
from studioflow.models import NormalizedIntake

def run():
    # Load input from file
    with open("input.json", "r") as f:
        data = json.load(f)

    intake = NormalizedIntake(**data)

    result = generate_project_output(intake)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run()
