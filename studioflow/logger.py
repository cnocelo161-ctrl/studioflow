import json
from datetime import datetime, timezone

from config import LOG_PATH


def log_entry(*, route, action, outcome, status, error_type, duration_ms):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "route": route,
        "action": action,
        "outcome": outcome,
        "status": status,
        "error_type": error_type,
        "duration_ms": duration_ms,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")


def log_review_action(*, review_id, action, review_state, rejection_reason):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "review_action",
        "review_id": review_id,
        "action": action,
        "review_state": review_state,
        "rejection_reason": rejection_reason,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")
