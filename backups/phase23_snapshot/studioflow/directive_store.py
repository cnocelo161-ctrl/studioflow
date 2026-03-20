import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from file_lock import file_lock
from models import DirectiveInput, DirectiveRecord

_store: Dict[str, DirectiveRecord] = {}

DIRECTIVE_PATH = Path(__file__).resolve().parent / "data" / "directives.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not DIRECTIVE_PATH.exists():
        return
    with file_lock(DIRECTIVE_PATH, exclusive=False):
        try:
            records = json.loads(DIRECTIVE_PATH.read_text())
            for record_dict in records:
                record = DirectiveRecord(**record_dict)
                _store[record.directive_id] = record
        except Exception as e:
            print(
                f"WARNING: directive_store: could not load {DIRECTIVE_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    DIRECTIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=DIRECTIVE_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(DIRECTIVE_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def create(inp: DirectiveInput) -> DirectiveRecord:
    with file_lock(DIRECTIVE_PATH, exclusive=True):
        record = DirectiveRecord(
            directive_id=str(uuid.uuid4()),
            created_at=_now(),
            **inp.model_dump(),
        )
        _store[record.directive_id] = record
        _flush()
    return record


def get(directive_id: str) -> DirectiveRecord:
    if directive_id not in _store:
        raise KeyError(directive_id)
    return _store[directive_id]


def list_all() -> List[DirectiveRecord]:
    return list(_store.values())


_load()
