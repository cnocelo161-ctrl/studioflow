"""
intake_sim.py — Intake simulation for StudioFlow.

Parses a plain-text email-style message, builds a /projects/run payload,
creates the project, client, and property records, then returns project_id.

Usage:
    python intake_sim.py

Email format (key: value, one per line):
    Client: <name>
    Address: <property address>
    Type: <project type>
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5001"


# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_email(text: str) -> dict:
    """Extract Client, Address, and Type from plain-text email body."""
    fields = {}
    for line in text.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().lower()] = value.strip()
    return {
        "client_name":      fields.get("client", ""),
        "property_address": fields.get("address", ""),
        "project_type":     fields.get("type", ""),
    }


# ── HTTP helper ────────────────────────────────────────────────────────────────

def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# ── Main flow ──────────────────────────────────────────────────────────────────

def run_intake(email_text: str) -> str:
    parsed = parse_email(email_text)

    assert parsed["client_name"],      "Missing: Client"
    assert parsed["property_address"], "Missing: Address"
    assert parsed["project_type"],     "Missing: Type"

    # 1. Create project
    workflow_payload = {
        "proposal_intake": {
            "client_name":      parsed["client_name"],
            "property_address": parsed["property_address"],
            "map":              "",
            "lot":              "",
            "project_type":     parsed["project_type"],
            "billing_mode":     "hourly",
            "scope_phases":     ["pre_design", "SD", "DD", "CD", "contract", "CA"],
        },
        "program_payload": {
            "spaces": [
                {"name": "Living Room", "level": "First Floor",
                 "sf": 0, "width_ft": 0, "length_ft": 0,
                 "requirements": [], "adjacencies": []},
            ]
        },
        "field_report_payload": {
            "visit_date": "TBD", "visit_time": "TBD", "weather": "TBD",
            "approximate_temp_f": 0, "phase": "pre_design",
            "work_in_progress": "TBD",
            "parties_present": ["TBD"], "transmitted_to": ["TBD"],
            "observations": ["TBD"], "action_required": [],
            "old_items": [], "new_items": [], "site_photos": [],
        },
        "schedule_payload": {
            "finish_entries": [{"space_name": "Living Room", "level": "First Floor"}],
            "fixture_entries": [],
        },
    }

    project = post("/projects/run", workflow_payload)
    project_id = project["project_id"]

    # 2. Create client (best-effort)
    try:
        post("/clients", {
            "project_id":   project_id,
            "client_name":  parsed["client_name"],
            "home_address": parsed["property_address"],
            "home_email":   "placeholder@example.com",
        })
    except Exception as e:
        print(f"  [warn] client create failed: {e}")

    # 3. Create property (best-effort)
    try:
        post("/properties", {
            "project_id": project_id,
            "address":    parsed["property_address"],
            "town":       "Edgartown",
        })
    except Exception as e:
        print(f"  [warn] property create failed: {e}")

    return project_id


# ── Example ────────────────────────────────────────────────────────────────────

EXAMPLE_EMAIL = """
Subject: New residential project inquiry

Hi,

My wife and I are planning a renovation with a modest addition to our home in Edgartown and would like to discuss feasibility, scope, and next steps.

Client: Andrew & Claire Whitman
Address: 7 North Summer Street, Edgartown, MA
Type: Renovation + Addition

Please let us know what information you would need from us to get started.

Best,
Andrew Whitman
"""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            email_text = f.read().strip()
    else:
        email_text = EXAMPLE_EMAIL.strip()
    print("Input:")
    print(email_text)
    project_id = run_intake(email_text)
    print(f"project_id: {project_id}")
    print(f"UI: {BASE_URL}/ui/projects/{project_id}")
