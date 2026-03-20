# PROJECT_SNAPSHOT_PHASE17.md

## Snapshot Metadata

| Field           | Value                          |
|-----------------|-------------------------------|
| Phase           | 17 — Project-Centric UI        |
| Status          | COMPLETE AND LOCKED            |
| Test result     | 17/17 passing                  |
| Date recorded   | 2026-03-19                     |
| Python env      | `/Users/robertnocelo/openclaw/.venv` |
| Project root    | `/Users/robertnocelo/openclaw/` |
| App root        | `/Users/robertnocelo/openclaw/studioflow/` |

---

## System Capabilities

### 1. Workflow Engine
Four domain modules execute sequentially and independently. Each receives a `project_id`, runs its logic, and returns a typed Pydantic output model.

- `proposal.py` — generates a fee proposal from `Phase1IntakeInput`
- `program.py` — computes program of spaces from `ProgramInput`
- `field_report.py` — assembles a CA field report from `FieldReportInput`
- `schedule.py` — compiles finish and fixture schedule from `ScheduleInput`

### 2. Orchestrator
`orchestrator.py` dispatches single-phase execution via `POST /orchestrate`. Accepts `{ action, payload }`. Routes to the correct domain module. Returns `{ action, result }`.

### 3. End-to-End Execution
`workflow.py` runs all four phases in sequence with a shared `project_id`. Called by `POST /workflow` (one-off runner) and `POST /projects/run` (persisted project creation). Returns `WorkflowOutput`.

### 4. Interface API
`interface.py` is the Flask application. Exposes all routes. Handles `ValidationError` → 422 and unhandled exceptions → 500, always with structured JSON `{ error, status, detail }`.

### 5. Error Handling
- 422: Pydantic `ValidationError` — includes `errors` array from `e.errors()`
- 500: Unhandled exception — includes `detail` from `str(e)`
- 404: Store key miss — `{ error: "not_found", status: 404, detail: "..." }`
- 409: Invalid state transition on review — `{ error: "conflict", status: 409, detail: "..." }`

### 6. Audit Logging
`logger.py` writes NDJSON records to `data/studioflow.log`. One JSON object per line, append mode. Two event types:
- `route_call` — logged on every `/orchestrate` and `/workflow` request (action, outcome, status, duration_ms, error_type)
- `review_action` — logged on submit, approve, and reject (review_id, action, review_state, rejection_reason)

`GET /review/<id>`, `GET /reviews`, `GET /projects`, `GET /projects/<id>` are NOT audited.

### 7. Config Layer
`config.py` reads environment variables at import time. All have defaults; none are required.

| Variable              | Default                           | Type    |
|-----------------------|-----------------------------------|---------|
| `STUDIOFLOW_PORT`     | `5001`                            | int     |
| `STUDIOFLOW_DEBUG`    | `False`                           | bool    |
| `STUDIOFLOW_LOG_PATH` | `studioflow/data/studioflow.log`  | Path    |

Truthy values for `STUDIOFLOW_DEBUG`: `"true"`, `"1"`, `"yes"` (case-insensitive).

### 8. Packaging and Runbook
- `requirements.txt` at `openclaw/` — pinned runtime deps: `flask==3.1.3`, `pydantic==2.12.5`, `openai==2.29.0`
- `.env.example` at `openclaw/` — template for env var configuration
- `DEMO_RUNBOOK.md` at `openclaw/` — full operator runbook with setup, test, start, and demo steps
- `run_tests.py` at `openclaw/studioflow/` — discovers and runs all `test_phase*.py` files in sorted order via subprocess

### 9. Review System (Persistent)
`review_store.py` manages human review/approval control. In-memory dict (`_store`) backed by `data/reviews.json`.

- `submit(action, result)` → creates `ReviewRecord` with `state="pending"`
- `approve(review_id)` → transitions `pending` → `approved`, sets `decided_at`
- `reject(review_id, reason)` → transitions `pending` → `rejected`, sets `decided_at`, `rejection_reason`
- `get(review_id)` → raises `KeyError` if not found
- `list_all()` → returns records in insertion order

State transitions are enforced: double-approve or double-reject raises `ValueError` → 409.

Persistence: `_flush()` writes atomically (`mkstemp` + `Path.replace()`). `_load()` is called at module import. Malformed JSON leaves file untouched, produces stderr warning, results in empty store.

`ReviewAction` is constrained to exactly: `"generate_proposal"`, `"generate_program"`, `"generate_field_report"`, `"compile_schedule"`, `"workflow"`.

### 10. Project System (Persistent)
`project_store.py` persists workflow runs as `ProjectRecord` objects in `data/projects.json`. Same atomic write and fail-safe load pattern as review_store.

- `save(workflow_output: dict)` → extracts fields, creates `ProjectRecord`, flushes
- `get(project_id)` → raises `KeyError` if not found
- `list_all()` → returns records in creation order

`ProjectRecord` fields: `project_id`, `client_name`, `property_address`, `project_type`, `workflow_output`, `created_at`.

`workflow_output` is stored as the exact `WorkflowOutput.model_dump()` dict — no transformation.

`reviews` is a derived field computed at `GET /projects/<project_id>` response time by filtering `review_store.list_all()` for records where `result.project_id == project_id`. It is never persisted to `projects.json`.

### 11. UI (Project-Centric, Review-Integrated)
`ui.py` is a Flask Blueprint serving Jinja2 HTML templates. All data fetching is done client-side via vanilla JS `fetch()` — templates contain no server-side data injection except `project_id` on the detail view.

| Route                    | Template                  | Purpose                                      |
|--------------------------|---------------------------|----------------------------------------------|
| `GET /ui/`               | `dashboard.html`          | Health badge + nav                           |
| `GET /ui/projects`       | `projects.html`           | Project list table, clickable rows           |
| `GET /ui/projects/new`   | `projects_new.html`       | New project form → redirects to detail       |
| `GET /ui/projects/<id>`  | `project_detail.html`     | Metadata + workflow output + review actions  |
| `GET /ui/reviews`        | `reviews.html`            | Review queue with project column             |
| `GET /ui/workflow`       | `workflow.html`           | One-off workflow runner (Phase 14, unchanged)|

---

## Critical Architecture Decisions

### Core vs Domain Separation
Files in `studioflow/` are separated into:
- **Core**: `interface.py`, `orchestrator.py`, `workflow.py`, `models.py`, `logger.py`, `config.py`, `project_store.py`, `review_store.py`, `ui.py` — infrastructure, routing, persistence, models
- **Domain**: `proposal.py`, `program.py`, `field_report.py`, `schedule.py` — business logic only; no Flask imports, no store access

Domain modules must never import from core. Core modules may import from domain.

### Project = One Workflow Run (Immutable)
A `ProjectRecord` is created once by `POST /projects/run` and never mutated. It captures the full `WorkflowOutput` at creation time. There is no update or patch operation.

### Reviews Linked via `result.project_id`
`ReviewRecord.result` is the arbitrary dict passed at submit time. For workflow reviews, this is the full `WorkflowOutput` dict, which contains `project_id`. The review→project linkage is established by reading `r.result.get("project_id")` at query time — no foreign key is stored in `ReviewRecord` itself.

### `reviews` Derived at Response Time, Never Persisted
`GET /projects/<project_id>` computes `reviews` by filtering all review records in memory. The `projects.json` file never contains a `reviews` or `review_ids` field. This ensures the project file is a pure, append-only record of workflow runs.

### Persistence Files
| File                         | Contents                          | Format         |
|------------------------------|-----------------------------------|----------------|
| `data/reviews.json`          | List of `ReviewRecord` dicts      | JSON array     |
| `data/projects.json`         | List of `ProjectRecord` dicts     | JSON array     |
| `data/studioflow.log`        | Audit log                         | NDJSON         |

### Atomic File Writes
Both `review_store._flush()` and `project_store._flush()` use:
```python
fd, tmp_name = tempfile.mkstemp(dir=TARGET.parent, suffix=".tmp")
with os.fdopen(fd, "w") as f:
    f.write(data)
Path(tmp_name).replace(TARGET)
```
On exception, the temp file is deleted. The target file is never partially written.

### No Database (Intentional)
All persistence is plain JSON files. This is an explicit design decision for the demo context — no SQLite, no external datastore, no ORM. The file-based approach is sufficient for single-operator use and keeps the system self-contained.

### Patchability
All file path constants (`LOG_PATH`, `REVIEW_PATH`, `PROJECT_PATH`) are module-level names. Tests patch them with `unittest.mock.patch` to redirect I/O to temp files, enabling full integration testing without touching the real data directory.

---

## File Structure

```
openclaw/
├── requirements.txt
├── .env.example
├── DEMO_RUNBOOK.md
├── PROJECT_SNAPSHOT_PHASE17.md
└── studioflow/
    ├── interface.py          # Flask app, all routes
    ├── orchestrator.py       # Single-phase dispatch
    ├── workflow.py           # End-to-end four-phase runner
    ├── models.py             # All Pydantic models
    ├── project_store.py      # Project persistence
    ├── review_store.py       # Review persistence
    ├── logger.py             # NDJSON audit log
    ├── config.py             # Env-driven config
    ├── ui.py                 # Flask Blueprint, HTML routes
    ├── run_tests.py          # Test runner
    ├── proposal.py           # Domain: fee proposal
    ├── program.py            # Domain: program of spaces
    ├── field_report.py       # Domain: CA field report
    ├── schedule.py           # Domain: finish/fixture schedule
    ├── intake.py             # Legacy intake helper
    ├── processor.py          # Legacy processor helper
    ├── app.py                # Legacy entry point
    ├── test_phase1.py        # Phase 1 tests
    ├── test_phase2.py        # Phase 2 tests
    ├── test_phase3.py        # Phase 3 tests
    ├── test_phase4.py        # Phase 4 tests
    ├── test_phase5.py        # Phase 5 tests
    ├── test_phase6.py        # Phase 6 tests
    ├── test_phase7.py        # Phase 7 tests
    ├── test_phase8.py        # Phase 8 tests
    ├── test_phase9.py        # Phase 9 tests
    ├── test_phase10.py       # Phase 10 tests
    ├── test_phase11.py       # Phase 11 tests
    ├── test_phase12.py       # Phase 12 tests
    ├── test_phase13.py       # Phase 13 tests
    ├── test_phase14.py       # Phase 14 tests
    ├── test_phase15.py       # Phase 15 tests
    ├── test_phase16.py       # Phase 16 tests
    ├── test_phase17.py       # Phase 17 tests
    ├── templates/
    │   └── ui/
    │       ├── dashboard.html       # Health badge + nav
    │       ├── projects.html        # Project list
    │       ├── projects_new.html    # New project form
    │       ├── project_detail.html  # Project + reviews
    │       ├── reviews.html         # Review queue
    │       └── workflow.html        # One-off runner
    └── data/                        # Created at runtime
        ├── projects.json
        ├── reviews.json
        └── studioflow.log
```

---

## API Surface

### Backend Routes

| Method | Route                        | Description                                      | Success | Errors        |
|--------|------------------------------|--------------------------------------------------|---------|---------------|
| POST   | `/orchestrate`               | Single-phase dispatch                            | 200     | 422, 500      |
| POST   | `/workflow`                  | End-to-end four-phase run (no persistence)       | 200     | 422, 500      |
| POST   | `/projects/run`              | End-to-end run + persist project                 | 200     | 422, 500      |
| GET    | `/projects`                  | List all projects (summary, no workflow_output)  | 200     | —             |
| GET    | `/projects/<project_id>`     | Full project + derived reviews array             | 200     | 404           |
| POST   | `/review`                    | Submit result for human review                   | 200     | 422           |
| GET    | `/review/<review_id>`        | Get single review record                         | 200     | 404           |
| POST   | `/review/<review_id>/approve`| Approve a pending review                         | 200     | 404, 409      |
| POST   | `/review/<review_id>/reject` | Reject a pending review (optional reason body)   | 200     | 404, 409      |
| GET    | `/reviews`                   | List all reviews in insertion order              | 200     | —             |
| GET    | `/health`                    | Health check                                     | 200     | —             |

### Response Shapes

**`GET /projects` response:**
```json
{
  "projects": [
    {
      "project_id": "...",
      "client_name": "...",
      "property_address": "...",
      "project_type": "...",
      "created_at": "..."
    }
  ]
}
```

**`GET /projects/<id>` response:**
```json
{
  "project_id": "...",
  "client_name": "...",
  "property_address": "...",
  "project_type": "...",
  "workflow_output": { ... },
  "created_at": "...",
  "reviews": [
    {
      "review_id": "...",
      "action": "workflow",
      "result": { ... },
      "state": "pending",
      "submitted_at": "...",
      "decided_at": null,
      "rejection_reason": null
    }
  ]
}
```

**Error response (all error codes):**
```json
{
  "error": "validation_error | not_found | conflict | internal_error",
  "status": 422,
  "detail": "..."
}
```
422 responses also include `"errors": [...]` (Pydantic `e.errors()` array).

### UI Routes

| Method | Route                      | Template              |
|--------|----------------------------|-----------------------|
| GET    | `/ui/`                     | `dashboard.html`      |
| GET    | `/ui/projects`             | `projects.html`       |
| GET    | `/ui/projects/new`         | `projects_new.html`   |
| GET    | `/ui/projects/<project_id>`| `project_detail.html` |
| GET    | `/ui/reviews`              | `reviews.html`        |
| GET    | `/ui/workflow`             | `workflow.html`       |

---

## Run Instructions

All commands must be run from `openclaw/` with the venv active.

### Activate venv
```bash
cd /Users/robertnocelo/openclaw
source .venv/bin/activate
```

Verify:
```bash
which python
# Expected: /Users/robertnocelo/openclaw/.venv/bin/python
```

### Run all tests
```bash
python studioflow/run_tests.py
# Expected: Passed: 17/17
```

### Start the server
```bash
python studioflow/interface.py
# Listening on http://127.0.0.1:5001
```

### Open the UI
```
http://127.0.0.1:5001/ui/
```

### Health check (curl)
```bash
curl http://127.0.0.1:5001/health
# {"status": "ok"}
```

### Create a project (curl)
```bash
curl -s -X POST http://127.0.0.1:5001/projects/run \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_intake": {
      "client_name": "Demo Client",
      "property_address": "1 Demo Lane, Edgartown, MA",
      "map": "01", "lot": "01",
      "project_type": "New Construction",
      "scope_phases": ["pre_design", "SD", "DD"],
      "billing_mode": "hourly"
    },
    "program_payload": {
      "spaces": [{
        "name": "Living Room", "level": "First Floor",
        "width_ft": 18.0, "length_ft": 22.0, "sf": 396.0,
        "requirements": [], "adjacencies": []
      }]
    },
    "field_report_payload": {
      "visit_date": "2026-03-19", "visit_time": "10:00 AM",
      "weather": "Clear", "approximate_temp_f": 52.0,
      "phase": "CA", "work_in_progress": "Framing",
      "parties_present": ["GC"], "transmitted_to": ["Client"],
      "observations": ["On track"], "action_required": [],
      "old_items": [], "new_items": [], "site_photos": []
    },
    "schedule_payload": {
      "finish_entries": [{
        "space_name": "Living Room", "level": "First Floor",
        "flooring": "Oak", "tile": null, "paint_colors": "White"
      }],
      "fixture_entries": []
    }
  }' | python -m json.tool
```

### Emergency fallback (no venv activation)
```bash
/Users/robertnocelo/openclaw/.venv/bin/python studioflow/run_tests.py
```

---

## How to Restore This State

This section describes what must be true for this state to be considered intact.

### Test Gate
Run from `openclaw/` with venv active:
```bash
python studioflow/run_tests.py
```
**All 17 test files must pass.** Any failure means the state has been altered.

### Schema Integrity
The following models in `models.py` must not be changed:

- `ProjectRecord` — `project_id`, `client_name`, `property_address`, `project_type`, `workflow_output`, `created_at`
- `ProjectSummary` — `project_id`, `client_name`, `property_address`, `project_type`, `created_at`
- `ReviewRecord` — `review_id`, `action`, `result`, `state`, `submitted_at`, `decided_at`, `rejection_reason`
- `ReviewSubmit` — `action`, `result`
- `ReviewAction` — exactly the five literal values listed above
- `WorkflowOutput` — `project_id`, `proposal`, `program`, `field_report`, `schedule`, `generated_at`

### Route Integrity
All 11 backend routes and 6 UI routes listed above must be registered and return the documented status codes. No route may be renamed, removed, or have its response shape altered.

### Persistence Integrity
- `data/projects.json` must contain a JSON array of `ProjectRecord` dicts. No `reviews` or `review_ids` field may appear in persisted records.
- `data/reviews.json` must contain a JSON array of `ReviewRecord` dicts.
- `data/studioflow.log` must be NDJSON (one JSON object per line).

### Behavior Invariants
- `GET /projects/<id>` returns `reviews` (derived) — never `review_ids`
- `POST /projects/run` persists `workflow_output` as exact `model_dump()` output — no transformation
- All file writes are atomic (`mkstemp` + `replace`)
- Malformed JSON data files produce stderr warnings and empty in-memory stores, never crashes
- `ReviewAction` validation rejects any value outside the five known literals
- Double-approve or double-reject returns 409, not 500

---

*This snapshot was generated at Phase 17 completion. Do not modify this file when restoring — use it as a read-only reference.*
