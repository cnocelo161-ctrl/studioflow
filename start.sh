#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="${STUDIOFLOW_HOST:-127.0.0.1}"
PORT="${STUDIOFLOW_PORT:-5001}"

echo "StudioFlow — pre-flight checks..."

# ── Check 1: Gunicorn present in venv ─────────────────────────────────────────
if [ ! -f ".venv/bin/gunicorn" ]; then
    echo ""
    echo "ERROR: Gunicorn not found in .venv."
    echo "  Run: source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# ── Check 2: PID file — live or stale ─────────────────────────────────────────
if [ -f "studioflow.pid" ]; then
    EXISTING_PID=$(cat studioflow.pid)
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo ""
        echo "ERROR: StudioFlow is already running (PID ${EXISTING_PID})."
        echo "  Run ./stop.sh to stop it first."
        exit 1
    else
        echo "  WARNING: Stale PID file found (PID ${EXISTING_PID} is not running)."
        echo "  Removing stale studioflow.pid and continuing..."
        rm studioflow.pid
    fi
fi

# ── Check 3: Port conflict ─────────────────────────────────────────────────────
if lsof -i TCP:"${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    PORT_PIDS=$(lsof -i TCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null | tr '\n' ' ')
    echo ""
    echo "ERROR: Port ${PORT} is already in use (PID(s): ${PORT_PIDS% })."
    echo "  Identify the process: lsof -i TCP:${PORT} -sTCP:LISTEN"
    echo "  Then stop it, or set a different port: export STUDIOFLOW_PORT=5002"
    exit 1
fi

# ── Check 4: Create required directories ──────────────────────────────────────
mkdir -p "${SCRIPT_DIR}/studioflow/data"
mkdir -p "${SCRIPT_DIR}/studioflow/logs"
mkdir -p "${SCRIPT_DIR}/logs"

echo "  All checks passed."
echo ""
echo "StudioFlow — starting Gunicorn..."

# ── Start Gunicorn ─────────────────────────────────────────────────────────────
# --workers 1 --threads 1 is required.
# project_store and review_store use in-memory dicts per process.
# Multiple workers would cause divergent state and silent data loss.
"${SCRIPT_DIR}/.venv/bin/gunicorn" \
    --workers 1 \
    --threads 1 \
    --bind "${HOST}:${PORT}" \
    --chdir "${SCRIPT_DIR}/studioflow" \
    --access-logfile "${SCRIPT_DIR}/logs/access.log" \
    --error-logfile "${SCRIPT_DIR}/logs/error.log" \
    --pid "${SCRIPT_DIR}/studioflow.pid" \
    --daemon \
    interface:app

echo "  Status : running"
echo "  URL    : http://${HOST}:${PORT}/ui/"
echo "  PID    : $(cat "${SCRIPT_DIR}/studioflow.pid")"
echo "  Logs   : ${SCRIPT_DIR}/logs/"
echo ""
echo "  Stop   : ./stop.sh"
