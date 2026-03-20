import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import project_store
import review_store
from interface import app

client = app.test_client()

VALID_WORKFLOW_PAYLOAD = {
    "proposal_intake": {
        "client_name": "Demo Client",
        "property_address": "1 Demo Lane, Edgartown, MA",
        "map": "01",
        "lot": "01",
        "project_type": "New Construction",
        "scope_phases": ["pre_design", "SD", "DD"],
        "billing_mode": "hourly",
    },
    "program_payload": {
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
        ]
    },
    "field_report_payload": {
        "visit_date": "2026-03-19",
        "visit_time": "10:00 AM",
        "weather": "Clear",
        "approximate_temp_f": 52.0,
        "phase": "CA",
        "work_in_progress": "Framing",
        "parties_present": ["GC"],
        "transmitted_to": ["Client"],
        "observations": ["On track"],
        "action_required": [],
        "old_items": [],
        "new_items": [],
        "site_photos": [],
    },
    "schedule_payload": {
        "finish_entries": [
            {
                "space_name": "Living Room",
                "level": "First Floor",
                "flooring": "Oak",
                "tile": None,
                "paint_colors": "White",
            }
        ],
        "fixture_entries": [],
    },
}


def fresh_tmp(suffix=".json"):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    os.unlink(path)
    return Path(path)


# ── Case 1: GET /ui/ returns 200 ──────────────────────────────────────────────

r = client.get("/ui/")
assert r.status_code == 200

print("Case 1: GET /ui/ returns 200.")

# ── Case 2: GET /ui/projects returns 200 ──────────────────────────────────────

r = client.get("/ui/projects")
assert r.status_code == 200

print("Case 2: GET /ui/projects returns 200.")

# ── Case 3: GET /ui/projects/new returns 200 ──────────────────────────────────

r = client.get("/ui/projects/new")
assert r.status_code == 200

print("Case 3: GET /ui/projects/new returns 200.")

# ── Case 4: GET /ui/projects/<id> returns 200 ─────────────────────────────────

r = client.get("/ui/projects/some-project-id")
assert r.status_code == 200

print("Case 4: GET /ui/projects/<id> returns 200.")

# ── Case 5: GET /ui/reviews returns 200 ───────────────────────────────────────

r = client.get("/ui/reviews")
assert r.status_code == 200

print("Case 5: GET /ui/reviews returns 200.")

# ── Case 6: GET /ui/workflow returns 200 ──────────────────────────────────────

r = client.get("/ui/workflow")
assert r.status_code == 200

print("Case 6: GET /ui/workflow returns 200.")

# ── Case 7: GET /ui/projects/new is not shadowed by /<project_id> ─────────────

# "new" should not be treated as a project_id; both routes should return 200
r_new = client.get("/ui/projects/new")
r_real = client.get("/ui/projects/some-id")
assert r_new.status_code == 200
assert r_real.status_code == 200

print("Case 7: /ui/projects/new and /ui/projects/<id> both resolve correctly.")

# ── Case 8: GET /projects/<id> returns reviews array (full records) ───────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        assert r.status_code == 200
        project_id = r.get_json()["project_id"]
        workflow_output = r.get_json()["workflow_output"]

        # submit a review linked to this project
        r2 = client.post("/review", json={"action": "workflow", "result": workflow_output})
        assert r2.status_code == 200
        review_id = r2.get_json()["review_id"]

        r3 = client.get(f"/projects/{project_id}")
        assert r3.status_code == 200
        data = r3.get_json()

        # reviews is a list of full records, not just IDs
        assert "reviews" in data
        assert isinstance(data["reviews"], list)
        assert len(data["reviews"]) == 1

        rev = data["reviews"][0]
        assert rev["review_id"] == review_id
        assert rev["action"] == "workflow"
        assert rev["state"] == "pending"
        assert "submitted_at" in rev
        assert "result" in rev

        # review_ids must NOT appear
        assert "review_ids" not in data

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 8: GET /projects/<id> returns reviews as full records; review_ids absent.")

print("All Phase 17 tests passed.")
