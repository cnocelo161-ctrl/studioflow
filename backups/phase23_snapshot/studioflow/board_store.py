import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from file_lock import file_lock
from models import ReviewingBoardInput, ReviewingBoardRecord

_store: Dict[str, ReviewingBoardRecord] = {}

BOARD_PATH = Path(__file__).resolve().parent / "data" / "boards.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not BOARD_PATH.exists():
        return
    with file_lock(BOARD_PATH, exclusive=False):
        try:
            records = json.loads(BOARD_PATH.read_text())
            for record_dict in records:
                record = ReviewingBoardRecord(**record_dict)
                _store[record.board_id] = record
        except Exception as e:
            print(
                f"WARNING: board_store: could not load {BOARD_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=BOARD_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(BOARD_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def create(inp: ReviewingBoardInput) -> ReviewingBoardRecord:
    with file_lock(BOARD_PATH, exclusive=True):
        now = _now()
        record = ReviewingBoardRecord(
            board_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            **inp.model_dump(),
        )
        _store[record.board_id] = record
        _flush()
    return record


def get(board_id: str) -> ReviewingBoardRecord:
    if board_id not in _store:
        raise KeyError(board_id)
    return _store[board_id]


def list_all() -> List[ReviewingBoardRecord]:
    return list(_store.values())


_load()
