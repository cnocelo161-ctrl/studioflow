import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from file_lock import file_lock
from models import PropertyInput, PropertyRecord

_store: Dict[str, PropertyRecord] = {}

PROPERTY_PATH = Path(__file__).resolve().parent / "data" / "properties.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not PROPERTY_PATH.exists():
        return
    with file_lock(PROPERTY_PATH, exclusive=False):
        try:
            records = json.loads(PROPERTY_PATH.read_text())
            for record_dict in records:
                record = PropertyRecord(**record_dict)
                _store[record.property_id] = record
        except Exception as e:
            print(
                f"WARNING: property_store: could not load {PROPERTY_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    PROPERTY_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=PROPERTY_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(PROPERTY_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def create(inp: PropertyInput) -> PropertyRecord:
    with file_lock(PROPERTY_PATH, exclusive=True):
        record = PropertyRecord(
            property_id=str(uuid.uuid4()),
            created_at=_now(),
            **inp.model_dump(),
        )
        _store[record.property_id] = record
        _flush()
    return record


def get(property_id: str) -> PropertyRecord:
    if property_id not in _store:
        raise KeyError(property_id)
    return _store[property_id]


def list_all() -> List[PropertyRecord]:
    return list(_store.values())


_load()
