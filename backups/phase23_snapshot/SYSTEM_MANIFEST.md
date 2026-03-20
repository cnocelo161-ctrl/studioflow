# StudioFlow — System Manifest
## Phase 23A Snapshot

---

### 1. System Overview

StudioFlow is a local workflow automation system built for Sherman + Associates, a licensed architecture firm on Martha's Vineyard. It replaces manual document assembly with a structured backend that generates proposals, programs of spaces, field reports, and finish schedules — grounded in the firm's actual project template library. The system runs entirely on a local machine, requires no cloud infrastructure, and is designed to be operated by a single-operator practice during real client sessions.

The current architecture is a Flask HTTP server backed by JSON file stores. A workflow engine sequences architecture-domain processors (intake → program → field report → schedule) and produces structured output that can be reviewed, approved, and persisted. Phase 23 begins injecting real client-domain entities — Client, Property, ReviewingBoard, MeetingMinute, Directive — derived directly from the firm's extracted project template files.

---

### 2. Phase Status

| Phase | Description | Status |
|---|---|---|
| Phase 1 | StudioFlow intake + proposal generation | Complete |
| Phase 2 | Program of spaces | Complete |
| Phase 3 | Construction administration field report | Complete |
| Phase 4 | Finish and fixture schedule | Complete |
| Phase 5 | Workflow orchestrator | Complete |
| Phase 6 | End-to-end workflow | Complete |
| Phase 7 | Logging | Complete |
| Phase 8 | Audit trail | Complete |
| Phase 9 | Config management | Complete |
| Phase 10 | Error handling | Complete |
| Phase 11 | Processor layer | Complete |
| Phase 12 | Core state | Complete |
| Phase 13 | Human review / approval control | Complete |
| Phase 14 | Domain separation (core / domain boundary) | Complete |
| Phase 15 | UI scaffold | Complete |
| Phase 16 | Project store + persistence | Complete |
| Phase 17 | Project detail + review UI | Complete |
| Phase 18 | Core project state | Complete |
| Phase 19 | UI polish | Complete |
| Phase 20 | Gunicorn daemonized server | Complete |
| Phase 21 | Access control + concurrency safety | Complete |
| Phase 22 | Pilot readiness + preflight | Complete |
| Phase 23A | Domain models + stores (Client, Property, ReviewingBoard, MeetingMinute, Directive) | Complete |
| Phase 23B | Routes + tests for Phase 23A entities | Pending |

---

### 3. Modules Implemented

**Stores**

| Module | Data file | Entity |
|---|---|---|
| `project_store.py` | `data/projects.json` | ProjectRecord |
| `review_store.py` | `data/reviews.json` | ReviewRecord |
| `client_store.py` | `data/clients.json` | ClientRecord |
| `property_store.py` | `data/properties.json` | PropertyRecord |
| `board_store.py` | `data/boards.json` | ReviewingBoardRecord |
| `minute_store.py` | `data/minutes.json` | MeetingMinuteRecord |
| `directive_store.py` | `data/directives.json` | DirectiveRecord |

**Core modules**

`interface.py` · `orchestrator.py` · `workflow.py` · `processor.py` · `core_state.py` · `auth.py` · `file_lock.py` · `logger.py` · `config.py` · `app.py` · `ui.py`

**Domain processors**

`intake.py` · `proposal.py` · `program.py` · `field_report.py` · `schedule.py`

---

### 4. Data Model Summary

| Entity | Key fields | Source |
|---|---|---|
| Project | project_id, client_name, property_address, project_type, workflow_output | project_store |
| Review | review_id, action, result, state, submitted_at, decided_at | review_store |
| Client | client_id, project_id, client_name, home/office contact fields | client_store |
| Property | property_id, project_id, address, zoning, setbacks, SF, cost | property_store |
| ReviewingBoard | board_id, project_id, board_name, required, status, dates | board_store |
| MeetingMinute | minute_id, project_id, meeting_date, type, attendees, action_items | minute_store |
| Directive | directive_id, project_id, directive_number, date, description, trade | directive_store |

---

### 5. Key Capabilities

- **Project workflow execution** — structured intake → program → field report → schedule pipeline
- **Human-in-the-loop review** — submit, approve, reject workflow outputs with audit trail
- **Client domain records** — Client, Property, ReviewingBoard, MeetingMinute, Directive entities
- **UI dashboard** — browser-based project list, detail, review submission and approval
- **Local server deployment** — Gunicorn daemonized, PID management, start/stop/status scripts
- **Preflight check** — automated GO/NO-GO before client sessions (preflight.sh)
- **Backup and restore** — atomic snapshot and restore scripts (backup.sh / restore.sh)
- **Optional HTTP Basic Auth** — operator-configured via environment variables
- **Concurrency safety** — fcntl file locking on all JSON store reads and writes
- **Structured logging** — per-request audit log with route, action, outcome, duration
