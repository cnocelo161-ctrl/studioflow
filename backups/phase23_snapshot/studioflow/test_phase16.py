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


# ── Case 1: POST /projects/run returns 200 with required project fields ────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    assert r.status_code == 200
    data = r.get_json()
    assert "project_id" in data
    assert data["client_name"] == "Demo Client"
    assert data["property_address"] == "1 Demo Lane, Edgartown, MA"
    assert data["project_type"] == "New Construction"
    assert "created_at" in data
    assert "workflow_output" in data
    assert data["workflow_output"]["project_id"] == data["project_id"]

tmp.unlink(missing_ok=True)

print("Case 1: POST /projects/run returns 200 with full ProjectRecord.")

# ── Case 2: POST /projects/run with invalid payload → 422 ─────────────────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.post("/projects/run", json={"proposal_intake": {}, "program_payload": {}})
    assert r.status_code == 422
    assert r.get_json()["error"] == "validation_error"

tmp.unlink(missing_ok=True)

print("Case 2: POST /projects/run with invalid payload → 422.")

# ── Case 3: After run, projects.json exists with workflow_output intact ────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    assert r.status_code == 200
    response_data = r.get_json()

    assert tmp.exists()
    file_data = json.loads(tmp.read_text())
    assert len(file_data) == 1
    assert file_data[0]["project_id"] == response_data["project_id"]
    assert file_data[0]["workflow_output"] == response_data["workflow_output"]
    assert "review_ids" not in file_data[0]

tmp.unlink(missing_ok=True)

print("Case 3: projects.json written with workflow_output intact; review_ids absent from file.")

# ── Case 4: GET /projects returns summary list, workflow_output excluded ───────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

    r = client.get("/projects")
    assert r.status_code == 200
    projects = r.get_json()["projects"]
    assert len(projects) == 1
    assert "project_id" in projects[0]
    assert "client_name" in projects[0]
    assert "workflow_output" not in projects[0]
    assert "review_ids" not in projects[0]

tmp.unlink(missing_ok=True)

print("Case 4: GET /projects returns summary list without workflow_output.")

# ── Case 5: GET /projects/<project_id> returns full record ────────────────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    project_id = r.get_json()["project_id"]

    r = client.get(f"/projects/{project_id}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["project_id"] == project_id
    assert "workflow_output" in data
    assert "reviews" in data
    assert isinstance(data["reviews"], list)

tmp.unlink(missing_ok=True)

print("Case 5: GET /projects/<project_id> returns full record with review_ids.")

# ── Case 6: GET /projects/<unknown_id> → 404 ──────────────────────────────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.get("/projects/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"

tmp.unlink(missing_ok=True)

print("Case 6: GET /projects/<unknown_id> → 404.")

# ── Case 7: Two runs create two distinct project records ──────────────────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r1 = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    r2 = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    pid1 = r1.get_json()["project_id"]
    pid2 = r2.get_json()["project_id"]

    assert pid1 != pid2

    r = client.get("/projects")
    projects = r.get_json()["projects"]
    assert len(projects) == 2
    assert projects[0]["project_id"] == pid1
    assert projects[1]["project_id"] == pid2

tmp.unlink(missing_ok=True)

print("Case 7: two runs produce two distinct project records in creation order.")

# ── Case 8: Records survive restart ───────────────────────────────────────────

tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()

    r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
    pid = r.get_json()["project_id"]
    original_output = r.get_json()["workflow_output"]

    project_store._store.clear()
    project_store._load()

    assert pid in project_store._store
    reloaded = project_store._store[pid]
    assert reloaded.workflow_output == original_output
    assert reloaded.client_name == "Demo Client"

tmp.unlink(missing_ok=True)

print("Case 8: project records survive restart — loaded from disk.")

# ── Case 9: Malformed projects.json → empty store, no crash, file untouched ───

tmp = fresh_tmp()
tmp.write_text("not valid json {{{{")
original_content = tmp.read_text()

from io import StringIO
import sys

captured = StringIO()

with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()
    with patch("sys.stderr", captured):
        project_store._load()

    assert len(project_store._store) == 0
    assert tmp.read_text() == original_content
    assert tmp.exists()

tmp.unlink(missing_ok=True)

print("Case 9: malformed projects.json → empty store, no crash, file untouched.")

# ── Case 10: review_ids computed at response time, not persisted ──────────────

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

        r2 = client.post("/review", json={"action": "workflow", "result": workflow_output})
        assert r2.status_code == 200
        review_id = r2.get_json()["review_id"]

        r3 = client.get(f"/projects/{project_id}")
        assert r3.status_code == 200
        data = r3.get_json()
        assert any(r["review_id"] == review_id for r in data["reviews"])

        # verify reviews is NOT in the persisted file
        file_data = json.loads(proj_tmp.read_text())
        assert "reviews" not in file_data[0]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 10: review_ids computed at response time; absent from projects.json.")

print("All Phase 16 tests passed.")
