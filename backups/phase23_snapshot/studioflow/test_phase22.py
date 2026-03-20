import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Case 1: PILOT_RUNBOOK.md exists ──────────────────────────────────────────

assert (REPO_ROOT / "PILOT_RUNBOOK.md").exists(), "PILOT_RUNBOOK.md not found at repo root"
print("Case 1: PILOT_RUNBOOK.md exists.")

# ── Case 2: preflight.sh exists ──────────────────────────────────────────────

assert (REPO_ROOT / "preflight.sh").exists(), "preflight.sh not found at repo root"
print("Case 2: preflight.sh exists.")

# ── Case 3: preflight.sh is executable ───────────────────────────────────────

mode = (REPO_ROOT / "preflight.sh").stat().st_mode
assert mode & stat.S_IXUSR, "preflight.sh is not user-executable"
print("Case 3: preflight.sh is executable.")

# ── Case 4: preflight.sh contains gunicorn check ─────────────────────────────

preflight_text = (REPO_ROOT / "preflight.sh").read_text()
assert "gunicorn" in preflight_text, "preflight.sh does not contain a gunicorn check"
print("Case 4: preflight.sh contains gunicorn check.")

# ── Case 5: preflight.sh contains port check logic ───────────────────────────

assert "lsof" in preflight_text and "PORT" in preflight_text, \
    "preflight.sh does not contain port availability check logic"
print("Case 5: preflight.sh contains port check logic.")

# ── Case 6: preflight.sh exits 0 in the current environment ──────────────────

# STUDIOFLOW_PREFLIGHT_IN_TEST=1 tells preflight.sh to skip the nested test
# suite run, preventing infinite recursion (preflight → tests → preflight → …).
result = subprocess.run(
    [str(REPO_ROOT / "preflight.sh")],
    capture_output=True,
    text=True,
    cwd=str(REPO_ROOT),
    env={**os.environ, "STUDIOFLOW_PREFLIGHT_IN_TEST": "1"},
)
assert result.returncode == 0, (
    f"preflight.sh exited {result.returncode}\n"
    f"stdout:\n{result.stdout}\n"
    f"stderr:\n{result.stderr}"
)
print("Case 6: preflight.sh exits 0.")

print("All Phase 22 tests passed.")
