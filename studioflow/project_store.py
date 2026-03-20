import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from file_lock import file_lock
from models import ProjectRecord

_store: Dict[str, ProjectRecord] = {}

PROJECT_PATH = Path(__file__).resolve().parent / "data" / "projects.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> None:
    if not PROJECT_PATH.exists():
        return
    with file_lock(PROJECT_PATH, exclusive=False):
        try:
            records = json.loads(PROJECT_PATH.read_text())
            for record_dict in records:
                record = ProjectRecord(**record_dict)
                _store[record.project_id] = record
        except Exception as e:
            print(
                f"WARNING: project_store: could not load {PROJECT_PATH}: {e}",
                file=sys.stderr,
            )


def _flush() -> None:
    PROJECT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps([r.model_dump() for r in _store.values()], indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=PROJECT_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        Path(tmp_name).replace(PROJECT_PATH)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def save(workflow_output: dict) -> ProjectRecord:
    with file_lock(PROJECT_PATH, exclusive=True):
        project_id = workflow_output["project_id"]
        record = ProjectRecord(
            project_id=project_id,
            client_name=workflow_output["proposal"]["client"]["name"],
            property_address=workflow_output["proposal"]["client"]["property_address"],
            project_type=workflow_output["proposal"]["project_type"],
            workflow_output=workflow_output,
            created_at=_now(),
        )
        _store[project_id] = record
        _flush()
    return record


def get(project_id: str) -> ProjectRecord:
    if project_id not in _store:
        raise KeyError(project_id)
    return _store[project_id]


def list_all() -> List[ProjectRecord]:
    return list(_store.values())


_load()
