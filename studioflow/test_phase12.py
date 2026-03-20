from pathlib import Path

import run_tests
from interface import app

# ── Case 1: STUDIOFLOW_DIR resolves to studioflow/ ────────────────────────────

assert run_tests.STUDIOFLOW_DIR == Path(__file__).resolve().parent
assert run_tests.STUDIOFLOW_DIR.name == "studioflow"

print("Case 1: STUDIOFLOW_DIR resolves correctly.")

# ── Case 2: PROJECT_ROOT resolves to openclaw/ ────────────────────────────────

assert run_tests.PROJECT_ROOT == run_tests.STUDIOFLOW_DIR.parent
assert run_tests.PROJECT_ROOT.name == "openclaw"

print("Case 2: PROJECT_ROOT resolves correctly.")

# ── Case 3: requirements.txt exists at PROJECT_ROOT ───────────────────────────

assert (run_tests.PROJECT_ROOT / "requirements.txt").exists()

print("Case 3: requirements.txt exists at project root.")

# ── Case 4: DEMO_RUNBOOK.md exists at PROJECT_ROOT ───────────────────────────

assert (run_tests.PROJECT_ROOT / "DEMO_RUNBOOK.md").exists()

print("Case 4: DEMO_RUNBOOK.md exists at project root.")

# ── Case 5: test files discovered in sorted order ─────────────────────────────

files = run_tests.test_files
names = [f.name for f in files]
assert names == sorted(names)
assert all(n.startswith("test_phase") for n in names)

print("Case 5: test files discovered in sorted order.")

# ── Case 6: GET /health returns 200 and {"status": "ok"} ─────────────────────

client = app.test_client()
response = client.get("/health")
assert response.status_code == 200
assert response.get_json() == {"status": "ok"}

print("Case 6: GET /health returns 200 and {\"status\": \"ok\"}.")

print("All Phase 12 tests passed.")
