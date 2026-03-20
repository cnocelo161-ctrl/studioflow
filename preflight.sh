#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${STUDIOFLOW_PORT:-5001}"
PASS=true

echo "StudioFlow — pre-session preflight check"
echo ""

# ── Check 1: .venv exists ─────────────────────────────────────────────────────
if [ -d "${SCRIPT_DIR}/.venv" ]; then
    echo "[OK]   .venv found"
else
    echo "[FAIL] .venv not found — run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    PASS=false
fi

# ── Check 2: gunicorn exists in .venv ─────────────────────────────────────────
if [ -f "${SCRIPT_DIR}/.venv/bin/gunicorn" ]; then
    echo "[OK]   gunicorn found in .venv/bin"
else
    echo "[FAIL] gunicorn not found — run: source .venv/bin/activate && pip install -r requirements.txt"
    PASS=false
fi

# ── Check 3: port is free ─────────────────────────────────────────────────────
if lsof -i TCP:"${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    PORT_PIDS=$(lsof -i TCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null | tr '\n' ' ')
    echo "[FAIL] Port ${PORT} is already in use (PID: ${PORT_PIDS% }) — stop the blocking process first"
    PASS=false
else
    echo "[OK]   Port ${PORT} is free"
fi

# ── Check 4: studioflow/data directory is writable ────────────────────────────
DATA_DIR="${SCRIPT_DIR}/studioflow/data"
if mkdir -p "$DATA_DIR" 2>/dev/null && [ -w "$DATA_DIR" ]; then
    echo "[OK]   studioflow/data directory is writable"
else
    echo "[FAIL] studioflow/data directory could not be created or is not writable"
    PASS=false
fi

# ── Check 5: full test suite ──────────────────────────────────────────────────
# STUDIOFLOW_PREFLIGHT_IN_TEST is set by test_phase22.py to prevent infinite
# recursion (the test runs preflight.sh, which would otherwise run the test
# suite again, which would run preflight.sh again, and so on).
if [ "${STUDIOFLOW_PREFLIGHT_IN_TEST:-}" = "1" ]; then
    echo "[OK]   Test suite check skipped (running inside test environment)"
else
    echo ""
    echo "Running test suite..."
    if "${SCRIPT_DIR}/.venv/bin/python" studioflow/run_tests.py >/dev/null 2>&1; then
        echo "[OK]   All tests passed"
    else
        echo "[FAIL] Test suite has failures — run: .venv/bin/python studioflow/run_tests.py"
        PASS=false
    fi
fi

# ── Check 6: auth configuration ───────────────────────────────────────────────
AUTH_USER="${STUDIOFLOW_AUTH_USER:-}"
AUTH_HASH="${STUDIOFLOW_AUTH_PASSWORD_HASH:-}"

if [ -n "$AUTH_USER" ] && [ -n "$AUTH_HASH" ]; then
    echo "[OK]   Auth is configured (user: ${AUTH_USER})"
elif [ -z "$AUTH_USER" ] && [ -z "$AUTH_HASH" ]; then
    echo "[WARN] Auth is DISABLED — set STUDIOFLOW_AUTH_USER + STUDIOFLOW_AUTH_PASSWORD_HASH to enable"
else
    echo "[FAIL] Auth is partially configured — both STUDIOFLOW_AUTH_USER and STUDIOFLOW_AUTH_PASSWORD_HASH must be set or both must be blank"
    PASS=false
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
if [ "$PASS" = true ]; then
    echo "GO — system ready"
    exit 0
else
    echo "NO-GO — fix issues above"
    exit 1
fi
