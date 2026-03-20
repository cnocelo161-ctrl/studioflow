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


# ── Case 1: GET /projects/<id> includes `core` field ─────────────────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        r2 = client.get(f"/projects/{project_id}")
        assert r2.status_code == 200
        data = r2.get_json()
        assert "core" in data

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 1: GET /projects/<id> includes `core` field.")

# ── Case 2: core.project_id matches the project ───────────────────────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        data = client.get(f"/projects/{project_id}").get_json()
        assert data["core"]["project_id"] == project_id

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 2: core.project_id matches the project.")

# ── Case 3: status = active, review_required = False with no reviews ──────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        data = client.get(f"/projects/{project_id}").get_json()
        core = data["core"]
        assert core["status"] == "active"
        assert core["review_required"] is False
        assert core["pending_review_count"] == 0
        assert core["review_count"] == 0

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 3: status=active, review_required=False when no reviews.")

# ── Case 4: next_action = 'No reviews submitted' when no reviews ──────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        data = client.get(f"/projects/{project_id}").get_json()
        assert data["core"]["next_action"] == "No reviews submitted"

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 4: next_action='No reviews submitted' when no reviews.")

# ── Case 5: pending review → status=pending_review, review_required=True ──────

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

        data = client.get(f"/projects/{project_id}").get_json()
        core = data["core"]
        assert core["status"] == "pending_review"
        assert core["review_required"] is True
        assert core["pending_review_count"] == 1
        assert core["review_count"] == 1
        assert "1 review(s) pending decision" in core["next_action"]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 5: pending review → status=pending_review, review_required=True.")

# ── Case 6: after approve → status=reviewed, review_required=False ────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]
        workflow_output = r.get_json()["workflow_output"]

        r2 = client.post("/review", json={"action": "workflow", "result": workflow_output})
        review_id = r2.get_json()["review_id"]
        client.post(f"/review/{review_id}/approve")

        data = client.get(f"/projects/{project_id}").get_json()
        core = data["core"]
        assert core["status"] == "reviewed"
        assert core["review_required"] is False
        assert core["next_action"] == "All reviews complete"

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 6: after approve → status=reviewed, review_required=False.")

# ── Case 7: summary contains client name, address, and project type ───────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        data = client.get(f"/projects/{project_id}").get_json()
        summary = data["core"]["summary"]
        assert "Demo Client" in summary
        assert "1 Demo Lane, Edgartown, MA" in summary
        assert "New Construction" in summary

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 7: core.summary contains client name, address, and project type.")

# ── Case 8: last_activity_at advances after a review is submitted ─────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]
        workflow_output = r.get_json()["workflow_output"]

        before = client.get(f"/projects/{project_id}").get_json()["core"]["last_activity_at"]

        client.post("/review", json={"action": "workflow", "result": workflow_output})

        after = client.get(f"/projects/{project_id}").get_json()["core"]["last_activity_at"]
        assert after >= before  # last_activity_at must be at least as recent

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 8: last_activity_at advances after a review is submitted.")

# ── Case 9: `core` is present in GET /projects list (Phase 19 additive) ───────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        r = client.get("/projects")
        projects = r.get_json()["projects"]
        assert len(projects) == 1
        assert "core" in projects[0]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 9: `core` is present in GET /projects list (Phase 19 additive).")

# ── Case 10: `core` is NOT persisted in projects.json ────────────────────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        file_data = json.loads(proj_tmp.read_text())
        assert len(file_data) == 1
        assert "core" not in file_data[0]
        assert "reviews" not in file_data[0]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 10: `core` is NOT persisted in projects.json.")

# ── Case 11: all expected core fields are present and typed correctly ─────────

proj_tmp = fresh_tmp()
rev_tmp = fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        project_id = r.get_json()["project_id"]

        core = client.get(f"/projects/{project_id}").get_json()["core"]
        assert isinstance(core["project_id"], str)
        assert core["status"] in ("active", "pending_review", "reviewed")
        assert isinstance(core["summary"], str) and core["summary"]
        assert isinstance(core["review_required"], bool)
        assert isinstance(core["pending_review_count"], int)
        assert isinstance(core["review_count"], int)
        assert isinstance(core["next_action"], str) and core["next_action"]
        assert isinstance(core["created_at"], str) and core["created_at"]
        assert isinstance(core["last_activity_at"], str) and core["last_activity_at"]

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 11: all core fields present with correct types.")

print("All Phase 18 tests passed.")
