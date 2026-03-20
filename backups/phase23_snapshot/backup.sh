#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
BACKUP_DIR="${SCRIPT_DIR}/backups/${TIMESTAMP}"
DATA_DIR="${SCRIPT_DIR}/studioflow/data"

# ── Check: data directory exists ──────────────────────────────────────────────
if [ ! -d "$DATA_DIR" ]; then
    echo "ERROR: Data directory not found: ${DATA_DIR}"
    echo "  No data to back up."
    exit 1
fi

mkdir -p "$BACKUP_DIR"

# ── Copy data files ───────────────────────────────────────────────────────────
# Because project/review persistence uses full-file atomic replace, this backup
# captures a consistent full-file snapshot of whichever version exists at copy
# time. That is acceptable for this system.

BACKED_UP=0
for FILE in projects.json reviews.json; do
    if [ -f "${DATA_DIR}/${FILE}" ]; then
        cp "${DATA_DIR}/${FILE}" "${BACKUP_DIR}/${FILE}"
        echo "  Backed up: ${FILE}"
        BACKED_UP=$((BACKED_UP + 1))
    else
        echo "  Skipped (not found): ${FILE}"
    fi
done

# ── Also copy audit log if present ────────────────────────────────────────────
AUDIT_LOG="${SCRIPT_DIR}/studioflow/logs/audit.log"
if [ -f "$AUDIT_LOG" ]; then
    cp "$AUDIT_LOG" "${BACKUP_DIR}/audit.log"
    echo "  Backed up: audit.log"
fi

if [ "$BACKED_UP" -eq 0 ]; then
    rm -rf "$BACKUP_DIR"
    echo "WARNING: No data files found — nothing backed up."
    exit 0
fi

echo ""
echo "Backup complete: ${BACKUP_DIR}"
