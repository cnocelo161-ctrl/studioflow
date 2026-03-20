import importlib
import os
import stat
from pathlib import Path

# Root of the repo (one level above this file's directory)
REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Case 1: start.sh exists ───────────────────────────────────────────────────

assert (REPO_ROOT / "start.sh").exists(), "start.sh not found"
print("Case 1: start.sh exists.")

# ── Case 2: stop.sh exists ────────────────────────────────────────────────────

assert (REPO_ROOT / "stop.sh").exists(), "stop.sh not found"
print("Case 2: stop.sh exists.")

# ── Case 3: start.sh is executable ───────────────────────────────────────────

start_mode = (REPO_ROOT / "start.sh").stat().st_mode
assert start_mode & stat.S_IXUSR, "start.sh is not user-executable"
print("Case 3: start.sh is executable.")

# ── Case 4: stop.sh is executable ────────────────────────────────────────────

stop_mode = (REPO_ROOT / "stop.sh").stat().st_mode
assert stop_mode & stat.S_IXUSR, "stop.sh is not user-executable"
print("Case 4: stop.sh is executable.")

# ── Case 5: gunicorn in requirements.txt ─────────────────────────────────────

req_text = (REPO_ROOT / "requirements.txt").read_text()
assert "gunicorn" in req_text, "gunicorn not found in requirements.txt"
print("Case 5: gunicorn found in requirements.txt.")

# ── Case 6: STUDIOFLOW_HOST in .env.example ──────────────────────────────────

env_example = (REPO_ROOT / ".env.example").read_text()
assert "STUDIOFLOW_HOST" in env_example, "STUDIOFLOW_HOST not found in .env.example"
print("Case 6: STUDIOFLOW_HOST found in .env.example.")

# ── Case 7: INTERFACE_HOST exported as str ────────────────────────────────────

import config
assert isinstance(config.INTERFACE_HOST, str), "INTERFACE_HOST is not a str"
print("Case 7: INTERFACE_HOST is a str.")

# ── Case 8: INTERFACE_HOST defaults to 127.0.0.1 when env var absent ─────────

env_backup = os.environ.pop("STUDIOFLOW_HOST", None)
importlib.reload(config)
assert config.INTERFACE_HOST == "127.0.0.1", f"Expected 127.0.0.1, got {config.INTERFACE_HOST!r}"
if env_backup is not None:
    os.environ["STUDIOFLOW_HOST"] = env_backup
importlib.reload(config)
print("Case 8: INTERFACE_HOST defaults to 127.0.0.1.")

# ── Case 9: INTERFACE_DEBUG defaults to False ─────────────────────────────────

env_debug_backup = os.environ.pop("STUDIOFLOW_DEBUG", None)
importlib.reload(config)
assert config.INTERFACE_DEBUG is False, "INTERFACE_DEBUG should default to False"
if env_debug_backup is not None:
    os.environ["STUDIOFLOW_DEBUG"] = env_debug_backup
importlib.reload(config)
print("Case 9: INTERFACE_DEBUG defaults to False.")

# ── Case 10: `from interface import app` is a Flask instance ─────────────────

from flask import Flask
from interface import app
assert isinstance(app, Flask), "app is not a Flask instance"
print("Case 10: interface.app is a Flask instance.")

print("All Phase 20 tests passed.")
