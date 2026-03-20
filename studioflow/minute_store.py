import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from file_lock import file_lock
from models import MeetingMinuteInput, MeetingMinuteRecord

_store: Dict[str, MeetingMinuteRecord] = {}

MINUTE_PATH = Path(__file__).resolve().parent / "data" / "minutes.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not MINUTE_PATH.exists():
        return
    with file_lock(MINUTE_PATH, exclusive=False):
        try:
            records = json.loads(MINUTE_PATH.read_text())
            for record_dict in records:
                record = MeetingMinuteRecord(**record_dict)
                _store[record.minute_id] = record
        except Exception as e:
            print(
                f"WARNING: minute_store: could not load {MINUTE_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    MINUTE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=MINUTE_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(MINUTE_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def create(inp: MeetingMinuteInput) -> MeetingMinuteRecord:
    with file_lock(MINUTE_PATH, exclusive=True):
        record = MeetingMinuteRecord(
            minute_id=str(uuid.uuid4()),
            created_at=_now(),
            **inp.model_dump(),
        )
        _store[record.minute_id] = record
        _flush()
    return record


def get(minute_id: str) -> MeetingMinuteRecord:
    if minute_id not in _store:
        raise KeyError(minute_id)
    return _store[minute_id]


def list_all() -> List[MeetingMinuteRecord]:
    return list(_store.values())


_load()
