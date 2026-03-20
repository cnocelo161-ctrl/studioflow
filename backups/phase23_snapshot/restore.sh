#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKUP_DIR="$1"

# ── Usage check ───────────────────────────────────────────────────────────────
if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./restore.sh <backup_dir>"
    echo "  Example: ./restore.sh backups/2026-03-19_142500"
    exit 1
fi

# Resolve to absolute path
if [[ "$BACKUP_DIR" != /* ]]; then
    BACKUP_DIR="${SCRIPT_DIR}/${BACKUP_DIR}"
fi

# ── Check: backup directory exists ────────────────────────────────────────────
if [ ! -d "$BACKUP_DIR" ]; then
    echo "ERROR: Backup directory not found: ${BACKUP_DIR}"
    exit 1
fi

# ── Check: backup contains at least one data file ─────────────────────────────
if [ ! -f "${BACKUP_DIR}/projects.json" ] && [ ! -f "${BACKUP_DIR}/reviews.json" ]; then
    echo "ERROR: No data files found in backup directory: ${BACKUP_DIR}"
    exit 1
fi

# ── Check: server must be stopped ─────────────────────────────────────────────
if [ -f "${SCRIPT_DIR}/studioflow.pid" ]; then
    EXISTING_PID=$(cat "${SCRIPT_DIR}/studioflow.pid")
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "ERROR: StudioFlow is currently running (PID ${EXISTING_PID})."
        echo "  Stop it first: ./stop.sh"
        exit 1
    fi
fi

# ── Restore data files ────────────────────────────────────────────────────────
DATA_DIR="${SCRIPT_DIR}/studioflow/data"
mkdir -p "$DATA_DIR"

RESTORED=0
for FILE in projects.json reviews.json; do
    if [ -f "${BACKUP_DIR}/${FILE}" ]; then
        cp "${BACKUP_DIR}/${FILE}" "${DATA_DIR}/${FILE}"
        echo "  Restored: ${FILE}"
        RESTORED=$((RESTORED + 1))
    else
        echo "  Skipped (not in backup): ${FILE}"
    fi
done

echo ""
echo "Restore complete from: ${BACKUP_DIR}"
echo "  Start the server: ./start.sh"
