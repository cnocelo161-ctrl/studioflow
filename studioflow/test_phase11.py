import importlib
import os
from pathlib import Path
from unittest.mock import patch

import config


def reload():
    importlib.reload(config)


# ── Case 1: Defaults are correct with no env vars set ─────────────────────────

assert config.INTERFACE_PORT == 5001
assert config.INTERFACE_DEBUG is False
assert config.LOG_PATH.name == "audit.log"
assert config.LOG_PATH.is_absolute()

print("Case 1: defaults correct.")

# ── Case 2: STUDIOFLOW_PORT override ──────────────────────────────────────────

with patch.dict(os.environ, {"STUDIOFLOW_PORT": "8080"}):
    reload()
    assert config.INTERFACE_PORT == 8080
reload()

print("Case 2: STUDIOFLOW_PORT override works.")

# ── Case 3: Empty STUDIOFLOW_PORT falls back to default ───────────────────────

with patch.dict(os.environ, {"STUDIOFLOW_PORT": ""}):
    reload()
    assert config.INTERFACE_PORT == 5001
reload()

print("Case 3: empty STUDIOFLOW_PORT falls back to default.")

# ── Case 4: STUDIOFLOW_DEBUG truthy values ────────────────────────────────────

for val in ("1", "true", "True", "TRUE", "yes"):
    with patch.dict(os.environ, {"STUDIOFLOW_DEBUG": val}):
        reload()
        assert config.INTERFACE_DEBUG is True, f"Expected True for {val!r}"
reload()

print("Case 4: STUDIOFLOW_DEBUG truthy values parsed correctly.")

# ── Case 5: STUDIOFLOW_DEBUG falsy values ─────────────────────────────────────

for val in ("0", "false", "no", ""):
    with patch.dict(os.environ, {"STUDIOFLOW_DEBUG": val}):
        reload()
        assert config.INTERFACE_DEBUG is False, f"Expected False for {val!r}"
reload()

print("Case 5: STUDIOFLOW_DEBUG falsy values parsed correctly.")

# ── Case 6: STUDIOFLOW_LOG_PATH — absolute path ───────────────────────────────

with patch.dict(os.environ, {"STUDIOFLOW_LOG_PATH": "/tmp/studioflow_test.log"}):
    reload()
    assert config.LOG_PATH == Path("/tmp/studioflow_test.log")
reload()

print("Case 6: absolute STUDIOFLOW_LOG_PATH accepted.")

# ── Case 7: STUDIOFLOW_LOG_PATH — relative path resolved against cwd ──────────

with patch.dict(os.environ, {"STUDIOFLOW_LOG_PATH": "relative/audit.log"}):
    reload()
    assert config.LOG_PATH == Path.cwd() / "relative/audit.log"
    assert config.LOG_PATH.is_absolute()
reload()

print("Case 7: relative STUDIOFLOW_LOG_PATH resolved against cwd.")

# ── Case 8: Empty STUDIOFLOW_LOG_PATH falls back to default ───────────────────

with patch.dict(os.environ, {"STUDIOFLOW_LOG_PATH": ""}):
    reload()
    assert config.LOG_PATH.name == "audit.log"
    assert config.LOG_PATH.is_absolute()
reload()

print("Case 8: empty STUDIOFLOW_LOG_PATH falls back to default.")

# ── Case 9: logger.LOG_PATH remains patchable (Phase 10 compatibility) ────────

import logger
assert hasattr(logger, "LOG_PATH")

print("Case 9: logger.LOG_PATH remains patchable as module-level name.")

print("All Phase 11 tests passed.")
