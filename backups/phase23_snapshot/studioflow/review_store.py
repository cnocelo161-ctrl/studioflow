import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from file_lock import file_lock
from models import ReviewRecord

_store: Dict[str, ReviewRecord] = {}

REVIEW_PATH = Path(__file__).resolve().parent / "data" / "reviews.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not REVIEW_PATH.exists():
        return
    with file_lock(REVIEW_PATH, exclusive=False):
        try:
            records = json.loads(REVIEW_PATH.read_text())
            for record_dict in records:
                record = ReviewRecord(**record_dict)
                _store[record.review_id] = record
        except Exception as e:
            print(
                f"WARNING: review_store: could not load {REVIEW_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=REVIEW_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(REVIEW_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def submit(action: str, result: dict) -> ReviewRecord:
    with file_lock(REVIEW_PATH, exclusive=True):
        review_id = str(uuid.uuid4())
        record = ReviewRecord(
            review_id=review_id,
            action=action,
            result=result,
            state="pending",
            submitted_at=_now(),
            decided_at=None,
            rejection_reason=None,
        )
        _store[review_id] = record
        _flush()
    return record


def get(review_id: str) -> ReviewRecord:
    if review_id not in _store:
        raise KeyError(review_id)
    return _store[review_id]


def approve(review_id: str) -> ReviewRecord:
    with file_lock(REVIEW_PATH, exclusive=True):
        record = get(review_id)
        if record.state != "pending":
            raise ValueError(f"Review {review_id} is already {record.state}")
        record.state = "approved"
        record.decided_at = _now()
        _flush()
    return record


def reject(review_id: str, reason: Optional[str] = None) -> ReviewRecord:
    with file_lock(REVIEW_PATH, exclusive=True):
        record = get(review_id)
        if record.state != "pending":
            raise ValueError(f"Review {review_id} is already {record.state}")
        record.state = "rejected"
        record.decided_at = _now()
        record.rejection_reason = reason
        _flush()
    return record


def list_all() -> List[ReviewRecord]:
    return list(_store.values())


_load()
