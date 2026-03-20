#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Check: PID file exists ─────────────────────────────────────────────────────
if [ ! -f "studioflow.pid" ]; then
    echo "ERROR: studioflow.pid not found."
    echo "  StudioFlow does not appear to be running."
    echo "  If you believe it is, check manually: ps aux | grep gunicorn"
    exit 1
fi

PID=$(cat studioflow.pid)

# ── Check: process is actually running ────────────────────────────────────────
if ! kill -0 "$PID" 2>/dev/null; then
    echo "WARNING: PID ${PID} is not running (stale PID file)."
    rm studioflow.pid
    echo "  Removed stale studioflow.pid."
    exit 0
fi

# ── Stop ───────────────────────────────────────────────────────────────────────
kill "$PID"
rm studioflow.pid
echo "StudioFlow stopped (was PID ${PID})."
