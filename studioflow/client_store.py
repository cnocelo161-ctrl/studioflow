import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from file_lock import file_lock
from models import ClientInput, ClientRecord

_store: Dict[str, ClientRecord] = {}

CLIENT_PATH = Path(__file__).resolve().parent / "data" / "clients.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not CLIENT_PATH.exists():
        return
    with file_lock(CLIENT_PATH, exclusive=False):
        try:
            records = json.loads(CLIENT_PATH.read_text())
            for record_dict in records:
                record = ClientRecord(**record_dict)
                _store[record.client_id] = record
        except Exception as e:
            print(
                f"WARNING: client_store: could not load {CLIENT_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    CLIENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=CLIENT_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(CLIENT_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def create(inp: ClientInput) -> ClientRecord:
    with file_lock(CLIENT_PATH, exclusive=True):
        record = ClientRecord(
            client_id=str(uuid.uuid4()),
            created_at=_now(),
            **inp.model_dump(),
        )
        _store[record.client_id] = record
        _flush()
    return record


def get(client_id: str) -> ClientRecord:
    if client_id not in _store:
        raise KeyError(client_id)
    return _store[client_id]


def list_all() -> List[ClientRecord]:
    return list(_store.values())


_load()
