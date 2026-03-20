# StudioFlow Architecture

## Layer Definitions

StudioFlow is organized into three explicit layers. Every file belongs to exactly one layer.

---

### CORE

Generic, reusable project-state and system concerns. CORE files contain no architecture-specific logic and no Sherman + Associates domain knowledge.

**What belongs in CORE:**
- Project identity (`project_id`, `created_at`, `client_name`, `project_type`, `property_address`)
- Project state and status tracking
- Review control (submit, approve, reject, state machine)
- Audit logging
- Persistence mechanics (file I/O, atomic writes, fail-safe load)
- Config layer (env-driven)
- Routing shell (`interface.py`)
- UI shell (`ui.py`, templates)
- Test runner

**CORE files:**
| File | Role |
|---|---|
| `interface.py` | Flask app, all routes |
| `project_store.py` | Project persistence (JSON file, atomic writes) |
| `review_store.py` | Review persistence (JSON file, atomic writes) |
| `logger.py` | NDJSON audit log |
| `config.py` | Env-driven configuration |
| `ui.py` | Flask Blueprint, HTML routes |
| `run_tests.py` | Test runner |
| `models.py` → CORE section | `ProjectRecord`, `ProjectSummary`, `ReviewRecord`, `ReviewSubmit`, `ReviewAction` |

---

### DOMAIN

Architecture-specific workflow content. DOMAIN files contain all Sherman + Associates business logic, phase definitions, compensation rules, and project-type-specific outputs.

**What belongs in DOMAIN:**
- Proposal generation (fee schedule, scope of services, compensation)
- Program of spaces (rooms, levels, square footage)
- Construction Administration field reports (site visits, open items, observations)
- Finish and fixture schedules (flooring, tile, paint, fixtures)
- All S+A-specific fields, phase tokens, and billing modes

**DOMAIN files:**
| File | Role |
|---|---|
| `proposal.py` | Fee proposal generation |
| `program.py` | Program of spaces compilation |
| `field_report.py` | CA field report assembly |
| `schedule.py` | Finish and fixture schedule compilation |
| `models.py` → DOMAIN section | Phases 1–4 models (intake, proposal, program, field report, schedule) |

---

### BOUNDARY

Interface contracts between CORE and DOMAIN. Boundary models are owned by the CORE orchestration shell but reference domain output types to wire the four-phase workflow together.

**What belongs in BOUNDARY:**
- `WorkflowInput` — the single entry point for a full workflow run; embeds `Phase1IntakeInput` directly
- `WorkflowOutput` — the full result of one workflow run; embeds all four domain outputs
- `OrchestratorRequest` / `OrchestratorResponse` — generic dispatch envelope for single-phase execution

**BOUNDARY files:**
| File | Role |
|---|---|
| `orchestrator.py` | Single-phase dispatch shell — calls domain handlers, no domain logic |
| `workflow.py` | End-to-end execution shell — sequences domain modules, no domain logic |
| `models.py` → BOUNDARY section | `WorkflowInput`, `WorkflowOutput`, `OrchestratorRequest`, `OrchestratorResponse` |

---

## Dependency Direction Rule

```
DOMAIN ──────────────────────────► (nothing in CORE or BOUNDARY)

BOUNDARY ─────────────────────────► DOMAIN (calls handlers, embeds output types)

CORE ──────────────────────────────► BOUNDARY (stores workflow_output as Dict[str, Any])
                                   ► DOMAIN (only indirectly, via workflow_output blob)
```

**The enforced rule:**

> CORE may depend on boundary contracts that reference DOMAIN outputs, but DOMAIN must never depend on CORE persistence, review, logging, config, or UI modules.

In concrete terms:
- `proposal.py`, `program.py`, `field_report.py`, `schedule.py` must never import from `project_store`, `review_store`, `logger`, `config`, `interface`, or `ui`
- `project_store.py`, `review_store.py`, `logger.py`, `config.py` must never import domain-specific logic or models
- `orchestrator.py` and `workflow.py` may import domain handlers and models; this is their explicit purpose

---

## Known Coupling Points

These are deliberate couplings at the CORE/DOMAIN boundary. They are not bugs — they are the current interface design. Document before changing.

### 1. `WorkflowInput.proposal_intake: Phase1IntakeInput`
`WorkflowInput` (BOUNDARY) embeds `Phase1IntakeInput` (DOMAIN) as a typed field. The workflow runner and the `/projects/run` route both accept this shape. Changing this requires coordinating the workflow input contract.

### 2. `WorkflowOutput` embeds domain output types
`WorkflowOutput.proposal: ProposalOutput`, `.program: ProgramOutput`, `.field_report: FieldReportOutput`, `.schedule: ScheduleOutput` — all domain types. These are the result shape of one complete workflow run.

### 3. `project_store.save()` extracts domain fields from the workflow output dict
`project_store.save()` reads `workflow_output["proposal"]["client"]["name"]` and `["proposal"]["client"]["property_address"]` and `["proposal"]["project_type"]` to populate `ProjectRecord`. This is CORE code that knows the internal structure of a DOMAIN output. It works because `workflow_output` is always a `WorkflowOutput.model_dump()` at the point of call. This coupling is documented here and must not silently diverge.

---

## File Structure

```
studioflow/
├── ARCHITECTURE.md          ← this file
├── interface.py             [CORE]     Flask app, all routes
├── orchestrator.py          [BOUNDARY] Single-phase dispatch shell
├── workflow.py              [BOUNDARY] End-to-end execution shell
├── models.py                           DOMAIN + BOUNDARY + CORE sections (see file)
├── project_store.py         [CORE]     Project persistence
├── review_store.py          [CORE]     Review persistence
├── logger.py                [CORE]     NDJSON audit log
├── config.py                [CORE]     Env-driven configuration
├── ui.py                    [CORE]     Flask Blueprint, HTML routes
├── run_tests.py             [CORE]     Test runner
├── proposal.py              [DOMAIN]   Fee proposal generation
├── program.py               [DOMAIN]   Program of spaces
├── field_report.py          [DOMAIN]   CA field report
├── schedule.py              [DOMAIN]   Finish/fixture schedule
├── templates/ui/            [CORE]     HTML templates (UI shell)
└── data/                               Runtime persistence (created on first write)
    ├── projects.json                   ProjectRecord list (JSON array)
    ├── reviews.json                    ReviewRecord list (JSON array)
    └── studioflow.log                  Audit log (NDJSON)
```

---

## Rules for Future Development

1. **New domain module** — create a new `*.py` file in the DOMAIN layer. It must not import from any CORE file. Add its input/output models to the DOMAIN section of `models.py`. Register it in `orchestrator.py` `ACTION_MAP` if it is a dispatchable phase.

2. **New core concern** — create a new `*.py` file in the CORE layer (e.g., a new store). It must not import domain-specific models or logic beyond what it receives as opaque `Dict[str, Any]`.

3. **Changing `WorkflowInput` or `WorkflowOutput`** — these are BOUNDARY contracts. Any change cascades to `workflow.py`, `interface.py`, `project_store.save()`, and all test files that use `VALID_WORKFLOW_PAYLOAD`. Treat as a breaking change and test fully.

4. **Adding a second domain** (e.g., a different firm type) — create a parallel set of DOMAIN files. The CORE layer requires no changes. The BOUNDARY layer (`WorkflowInput`, `WorkflowOutput`) would need versioning or a discriminated union. Plan carefully before starting.

5. **`models.py` section discipline** — new models must be added to the correct labeled section (DOMAIN, BOUNDARY, or CORE). Do not add domain-specific fields to CORE models. Do not add CORE concerns (review state, project status) to DOMAIN models.
