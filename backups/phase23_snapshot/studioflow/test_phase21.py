import importlib
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

import auth
import project_store
import review_store
from interface import app

client = app.test_client()

REPO_ROOT = Path(__file__).resolve().parent.parent

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


def _fresh_tmp(suffix=".json"):
    import os
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    os.unlink(path)
    return Path(path)


def _set_auth_env(user, password_hash):
    os.environ["STUDIOFLOW_AUTH_USER"] = user
    os.environ["STUDIOFLOW_AUTH_PASSWORD_HASH"] = password_hash


def _clear_auth_env():
    os.environ.pop("STUDIOFLOW_AUTH_USER", None)
    os.environ.pop("STUDIOFLOW_AUTH_PASSWORD_HASH", None)


# ── Case 1: Auth disabled — protected route returns 200 ──────────────────────
# Auth vars are absent at test startup; auth module was loaded with AUTH_ENABLED=False.

assert not auth.AUTH_ENABLED, "AUTH_ENABLED should be False when vars are absent"
r = client.get("/projects")
assert r.status_code == 200

print("Case 1: auth disabled — protected route returns 200.")

# ── Case 2: Auth enabled, no credentials → 401 ───────────────────────────────

TEST_PASSWORD = "testpass"
TEST_HASH = generate_password_hash(TEST_PASSWORD, method="pbkdf2:sha256")
TEST_USER = "operator"

_set_auth_env(TEST_USER, TEST_HASH)
importlib.reload(auth)
assert auth.AUTH_ENABLED

r = client.get("/projects")
assert r.status_code == 401
assert r.headers.get("WWW-Authenticate") == 'Basic realm="StudioFlow"'

print("Case 2: auth enabled, no credentials → 401.")

# ── Case 3: Auth enabled, wrong password → 401 ───────────────────────────────

import base64

def basic_auth_header(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

r = client.get("/projects", headers=basic_auth_header(TEST_USER, "wrongpassword"))
assert r.status_code == 401

print("Case 3: auth enabled, wrong password → 401.")

# ── Case 4: Auth enabled, correct credentials → 200 ──────────────────────────

r = client.get("/projects", headers=basic_auth_header(TEST_USER, TEST_PASSWORD))
assert r.status_code == 200

print("Case 4: auth enabled, correct credentials → 200.")

# ── Case 5: /health exempt from auth — returns 200 with no credentials ────────

r = client.get("/health")
assert r.status_code == 200

print("Case 5: /health exempt from auth, returns 200 with no credentials.")

# ── Case 6: One var set without the other → RuntimeError on auth reload ───────

_clear_auth_env()
os.environ["STUDIOFLOW_AUTH_USER"] = "admin"
# STUDIOFLOW_AUTH_PASSWORD_HASH intentionally not set

try:
    importlib.reload(auth)
    assert False, "Expected RuntimeError for partial auth config"
except RuntimeError:
    pass
finally:
    _clear_auth_env()
    importlib.reload(auth)  # restore to disabled state

assert not auth.AUTH_ENABLED

print("Case 6: partial auth config → RuntimeError on reload.")

# ── Case 7: Lock file created alongside data file after a project store write ─

proj_tmp = _fresh_tmp()
rev_tmp = _fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)

        lock_path = Path(str(proj_tmp) + ".lock")
        assert lock_path.exists(), "projects.json.lock not created after write"
        lock_path.unlink(missing_ok=True)

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 7: lock file created alongside projects.json after a write.")

# ── Case 8: Lock file created alongside data file after a review store write ──

proj_tmp = _fresh_tmp()
rev_tmp = _fresh_tmp()

with patch("project_store.PROJECT_PATH", proj_tmp):
    with patch("review_store.REVIEW_PATH", rev_tmp):
        project_store._store.clear()
        review_store._store.clear()

        r = client.post("/projects/run", json=VALID_WORKFLOW_PAYLOAD)
        workflow_output = r.get_json()["workflow_output"]
        client.post("/review", json={"action": "workflow", "result": workflow_output})

        lock_path = Path(str(rev_tmp) + ".lock")
        assert lock_path.exists(), "reviews.json.lock not created after write"
        lock_path.unlink(missing_ok=True)

proj_tmp.unlink(missing_ok=True)
rev_tmp.unlink(missing_ok=True)

print("Case 8: lock file created alongside reviews.json after a write.")

# ── Case 9: backup.sh exists and is executable ────────────────────────────────

backup_sh = REPO_ROOT / "backup.sh"
assert backup_sh.exists(), "backup.sh not found"
assert backup_sh.stat().st_mode & stat.S_IXUSR, "backup.sh is not user-executable"

print("Case 9: backup.sh exists and is executable.")

# ── Case 10: restore.sh exists and is executable ─────────────────────────────

restore_sh = REPO_ROOT / "restore.sh"
assert restore_sh.exists(), "restore.sh not found"
assert restore_sh.stat().st_mode & stat.S_IXUSR, "restore.sh is not user-executable"

print("Case 10: restore.sh exists and is executable.")

print("All Phase 21 tests passed.")
