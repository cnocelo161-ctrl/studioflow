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


# ── Case 1: GET /projects includes `core` in each project summary ─────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        r = client.get("/projects")
        assert r.status_code == 200
        projects = r.get_json()["projects"]
        assert len(projects) == 1
        assert "core" in projects[0]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 1: GET /projects includes `core` in each project summary.")

# ── Case 2: core.status = active, review_required = False when no reviews ─────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        projects = client.get("/projects").get_json()["projects"]
        core = projects[0]["core"]
        assert core["status"] == "active"
        assert core["review_required"] is False
        assert core["pending_review_count"] == 0

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 2: core.status=active, review_required=False when no reviews.")

# ── Case 3: core.status = pending_review after a pending review is submitted ───

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        workflow_output = r.get_json()["workflow_output"]

        client.post("/review", json={"action": "workflow", "result": workflow_output})

        projects = client.get("/projects").get_json()["projects"]
        core = projects[0]["core"]
        assert core["status"] == "pending_review"
        assert core["review_required"] is True
        assert core["pending_review_count"] == 1

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 3: core.status=pending_review after a pending review is submitted.")

# ── Case 4: core.status = reviewed after the review is approved ───────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        workflow_output = r.get_json()["workflow_output"]

        r2 = client.post("/review", json={"action": "workflow", "result": workflow_output})
        review_id = r2.get_json()["review_id"]
        client.post(f"/review/{review_id}/approve")

        projects = client.get("/projects").get_json()["projects"]
        core = projects[0]["core"]
        assert core["status"] == "reviewed"
        assert core["review_required"] is False
        assert core["pending_review_count"] == 0

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 4: core.status=reviewed after approval.")

# ── Case 5: all existing GET /projects fields still present (non-regression) ───

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        p = client.get("/projects").get_json()["projects"][0]
        assert "project_id" in p
        assert "client_name" in p
        assert "property_address" in p
        assert "project_type" in p
        assert "created_at" in p
        assert "workflow_output" not in p   # summary — no workflow blob

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 5: all existing GET /projects fields present; workflow_output absent.")

# ── Case 6: GET /projects with zero projects returns empty list ────────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.get("/projects")
        assert r.status_code == 200
        assert r.get_json() == {"projects": []}

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 6: GET /projects with zero projects returns empty list.")

# ── Case 7: core in list matches core in detail for same project ──────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]
        workflow_output = r.get_json()["workflow_output"]

        client.post("/review", json={"action": "workflow", "result": workflow_output})

        list_core = client.get("/projects").get_json()["projects"][0]["core"]
        detail_core = client.get(f"/projects/{project_id}").get_json()["core"]

        assert list_core["status"] == detail_core["status"]
        assert list_core["review_required"] == detail_core["review_required"]
        assert list_core["pending_review_count"] == detail_core["pending_review_count"]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 7: core in list matches core in detail for the same project.")

# ── Case 8: UI routes still return 200 (non-regression) ──────────────────────

r = client.get("/ui/projects")
assert r.status_code == 200

r = client.get("/ui/projects/some-id")
assert r.status_code == 200

print("Case 8: UI routes still return 200 (non-regression).")

print("All Phase 19 tests passed.")
