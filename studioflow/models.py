from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Dict, List, Literal, Optional


# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN MODELS
# Architecture-specific workflow content — Sherman + Associates only.
# These models must never depend on CORE persistence, logging, config, or UI.
# ══════════════════════════════════════════════════════════════════════════════

class ProjectIntakeInput(BaseModel):
    action: str = Field(..., description="Must be 'project_intake'")
    client_name: str = Field(default="")
    project_type: str = Field(default="")
    location: str = Field(default="")
    description: str = Field(default="")
    budget: str = Field(default="")
    timeline: str = Field(default="")

    @field_validator("action")
    @classmethod
    def action_must_be_project_intake(cls, v: str) -> str:
        if v != "project_intake":
            raise ValueError("action must be 'project_intake'")
        return v

    def normalize(self) -> "NormalizedIntake":
        return NormalizedIntake(
            client_name=self.client_name.strip() or None,
            project_type=self.project_type.strip() or None,
            location=self.location.strip() or None,
            description=self.description.strip() or None,
            budget=self.budget.strip() or None,
            timeline=self.timeline.strip() or None,
        )


class NormalizedIntake(BaseModel):
    client_name: Optional[str]
    project_type: Optional[str]
    location: Optional[str]
    description: Optional[str]
    budget: Optional[str]
    timeline: Optional[str]


# ── Phase 1: StudioFlow Intake + Proposal Models  [DOMAIN] ───────────────────

_PHASE_ORDER_LOCAL = ("pre_design", "SD", "DD", "CD", "contract", "CA")
_FIXED_FEE_NATIVE_LOCAL = {"DD", "CD", "contract", "CA"}

PhaseToken = Literal["pre_design", "SD", "DD", "CD", "contract", "CA"]


class Phase1IntakeInput(BaseModel):
    client_name: str
    property_address: str
    map: str
    lot: str
    project_type: str
    scope_phases: List[PhaseToken]
    billing_mode: Literal["hourly", "fixed_fee", "hybrid"]
    probable_cost: Optional[float] = None

    @field_validator("scope_phases")
    @classmethod
    def deduplicate_and_order(cls, v: List[str]) -> List[str]:
        seen = set()
        ordered = []
        for token in _PHASE_ORDER_LOCAL:
            if token in v and token not in seen:
                seen.add(token)
                ordered.append(token)
        if not ordered:
            raise ValueError("scope_phases must contain at least one valid phase token")
        return ordered

    @model_validator(mode="after")
    def require_probable_cost_for_fixed_fee(self) -> "Phase1IntakeInput":
        if self.billing_mode in ("fixed_fee", "hybrid"):
            has_fixed_fee_phase = any(p in _FIXED_FEE_NATIVE_LOCAL for p in self.scope_phases)
            if has_fixed_fee_phase and self.probable_cost is None:
                raise ValueError("probable_cost is required when fixed-fee phases are included")
        return self


class PhaseService(BaseModel):
    phase_code: str
    phase_token: str
    name: str
    billing_type: str
    tasks: List[str]


class HourlyRates(BaseModel):
    founding_principal: float = 225.0
    design_principal: float = 225.0
    senior_associate: float = 185.0
    associate: float = 165.0
    project_administration: float = 125.0


class Compensation(BaseModel):
    billing_mode: str
    hourly_phases: List[str]
    fixed_fee_phases: List[str]
    hourly_rates: HourlyRates
    fixed_fee_percent: Optional[float]
    probable_cost: Optional[float]
    fixed_fee_total: Optional[float]


class ClientInfo(BaseModel):
    name: str
    property_address: str
    map: str
    lot: str


class ProposalOutput(BaseModel):
    proposal_id: str
    project_id: str
    client: ClientInfo
    project_type: str
    scope_of_services: List[PhaseService]
    compensation: Compensation
    document_ready: bool = True
    generated_at: str


# ── Phase 2: Program of Spaces Models  [DOMAIN] ───────────────────────────────

class ProgramSpace(BaseModel):
    name: str
    level: str
    width_ft: float
    length_ft: float
    sf: float
    requirements: List[str]
    adjacencies: List[str]


class ProgramInput(BaseModel):
    project_id: str
    spaces: List[ProgramSpace]
    design_intent: Optional[str] = None
    additional_notes: Optional[List[str]] = None


class ProgramOutput(BaseModel):
    program_id: str
    project_id: str
    net_sf: float
    circulation_factor: float = 0.10
    gross_sf: float
    spaces_by_level: Dict[str, List[ProgramSpace]]
    document_ready: bool = True
    generated_at: str


# ── Phase 3: Construction Administration Field Report Models  [DOMAIN] ────────

class FieldReportItem(BaseModel):
    item_number: str
    description: str
    responsible_party: Optional[str] = None  # may be unassigned at time of report
    status: Literal["open", "closed", "in_progress"]

    @field_validator("item_number", "description")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class FieldReportInput(BaseModel):
    project_id: str
    visit_date: str   # plain str — non-empty enforced; no format parsing
    visit_time: str   # plain str — non-empty enforced; no format parsing
    weather: str
    approximate_temp_f: float
    phase: str
    work_in_progress: str
    parties_present: List[str]   # min 1 entry required
    transmitted_to: List[str]    # min 1 entry required
    observations: List[str]      # min 1 entry required
    action_required: List[str]   # can be empty
    old_items: List[FieldReportItem]   # empty on first site visit
    new_items: List[FieldReportItem]   # can be empty
    site_photos: List[str]             # can be empty

    @field_validator("visit_date", "visit_time")
    @classmethod
    def must_be_non_empty_str(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v

    @field_validator("parties_present", "transmitted_to", "observations")
    @classmethod
    def must_have_at_least_one(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("list must contain at least one entry")
        return v

    @model_validator(mode="after")
    def item_numbers_must_be_unique(self) -> "FieldReportInput":
        all_numbers = [item.item_number for item in self.old_items + self.new_items]
        if len(all_numbers) != len(set(all_numbers)):
            duplicates = {n for n in all_numbers if all_numbers.count(n) > 1}
            raise ValueError(f"item_number must be unique across old_items and new_items — duplicates: {duplicates}")
        return self


class FieldReportOutput(BaseModel):
    report_id: str
    project_id: str
    visit_date: str
    visit_time: str
    weather: str
    approximate_temp_f: float
    phase: str
    work_in_progress: str
    parties_present: List[str]
    transmitted_to: List[str]
    observations: List[str]
    action_required: List[str]
    old_items: List[FieldReportItem]
    new_items: List[FieldReportItem]
    open_item_count: int  # count where status is "open" or "in_progress"; 0 if both lists empty
    site_photos: List[str]
    document_ready: bool = True
    generated_at: str


# ── Phase 4: Finish & Fixture Schedule Models  [DOMAIN] ──────────────────────
#
# Source-grounded fields (Proposal for Services §1.4 CD task 6):
#   FinishEntry: flooring, tile, paint_colors
#   FixtureEntry.fixture_type values: electrical, plumbing, cabinet, hardware, appliance
#
# Provisional internal fields (NOT from retrieved S+A documents — functional scaffolding only):
#   FinishEntry: notes
#   FixtureEntry: manufacturer, model_number, finish_color, locations, quantity, notes
#
# Provisional fields must be validated against actual S+A schedule templates before
# this schema is considered source-confirmed.

class FinishEntry(BaseModel):
    # compiler-required
    space_name: str
    level: str
    # source-grounded — Proposal for Services §1.4 CD task 6
    flooring: Optional[str] = None
    tile: Optional[str] = None
    paint_colors: Optional[str] = None
    # provisional — not in retrieved S+A documents
    notes: Optional[str] = None

    @field_validator("space_name", "level")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class FixtureEntry(BaseModel):
    # compiler-required
    fixture_id: str
    # source-grounded — Proposal for Services §1.4 CD task 6
    fixture_type: Literal["electrical", "plumbing", "cabinet", "hardware", "appliance"]
    # compiler-required (minimum usable field)
    description: str
    # provisional — not in retrieved S+A documents; functional scaffolding only
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    finish_color: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    quantity: int = 1
    notes: Optional[str] = None

    @field_validator("fixture_id", "description")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("quantity must be at least 1")
        return v


class ScheduleInput(BaseModel):
    project_id: str
    finish_entries: List[FinishEntry]   # min 1 entry required
    fixture_entries: List[FixtureEntry] = Field(default_factory=list)  # can be empty — selections may be deferred
    additional_notes: Optional[List[str]] = None

    @field_validator("finish_entries")
    @classmethod
    def must_have_at_least_one_finish(cls, v: List[FinishEntry]) -> List[FinishEntry]:
        if not v:
            raise ValueError("finish_entries must contain at least one space")
        return v

    @model_validator(mode="after")
    def check_uniqueness(self) -> "ScheduleInput":
        space_names = [e.space_name for e in self.finish_entries]
        if len(space_names) != len(set(space_names)):
            dupes = {n for n in space_names if space_names.count(n) > 1}
            raise ValueError(f"space_name must be unique across finish_entries — duplicates: {dupes}")
        fixture_ids = [f.fixture_id for f in self.fixture_entries]
        if len(fixture_ids) != len(set(fixture_ids)):
            dupes = {i for i in fixture_ids if fixture_ids.count(i) > 1}
            raise ValueError(f"fixture_id must be unique across fixture_entries — duplicates: {dupes}")
        return self


class ScheduleOutput(BaseModel):
    schedule_id: str
    project_id: str
    finish_by_level: Dict[str, List[FinishEntry]]
    fixtures_by_type: Dict[str, List[FixtureEntry]]
    total_fixture_count: int  # computed — sum of all FixtureEntry.quantity; 0 if no fixtures
    document_ready: bool = True
    generated_at: str


# ══════════════════════════════════════════════════════════════════════════════
# BOUNDARY MODELS
# Interface contracts between CORE and DOMAIN.
# CORE orchestration shells reference these models to invoke domain handlers.
# Changing these models requires coordinating both layers.
# ══════════════════════════════════════════════════════════════════════════════

# ── Phase 5: Workflow Orchestrator Models  [BOUNDARY] ─────────────────────────

class OrchestratorRequest(BaseModel):
    action: Literal[
        "generate_proposal",
        "generate_program",
        "generate_field_report",
        "compile_schedule",
    ]
    payload: Dict[str, Any]


class OrchestratorResponse(BaseModel):
    action: str
    result: BaseModel
    # No generated_at — each phase output already contains its own timestamp.
    # The orchestrator adds no metadata beyond the action wrapper.

    # result is typed as BaseModel to keep the orchestrator domain-agnostic.
    # Pydantic v2 serializes by declared type, so BaseModel would otherwise dump as {}.
    # This override delegates serialization to the concrete runtime model instance.
    def model_dump(self, **kwargs):
        d = super().model_dump(**kwargs)
        d["result"] = self.result.model_dump(**kwargs)
        return d


# ── Phase 6: End-to-End Workflow Models  [BOUNDARY] ──────────────────────────

class WorkflowInput(BaseModel):
    proposal_intake: Phase1IntakeInput
    program_payload: Dict[str, Any]       # ProgramInput fields excluding project_id
    field_report_payload: Dict[str, Any]  # FieldReportInput fields excluding project_id
    schedule_payload: Dict[str, Any]      # ScheduleInput fields excluding project_id


class WorkflowOutput(BaseModel):
    project_id: str
    proposal: ProposalOutput
    program: ProgramOutput
    field_report: FieldReportOutput
    schedule: ScheduleOutput
    generated_at: str  # workflow-level UTC ISO timestamp


# ══════════════════════════════════════════════════════════════════════════════
# CORE MODELS
# Generic, reusable project-state and system concerns.
# These models must never embed architecture-specific domain logic.
# ══════════════════════════════════════════════════════════════════════════════

# ── Phase 16: Project Store Models  [CORE] ────────────────────────────────────

class ProjectSummary(BaseModel):
    project_id: str
    client_name: str
    property_address: str
    project_type: str
    created_at: str


class ProjectRecord(BaseModel):
    project_id: str
    client_name: str
    property_address: str
    project_type: str
    workflow_output: Dict[str, Any]
    created_at: str


# ── Phase 13: Human Review / Approval Control Models  [CORE] ─────────────────

ReviewAction = Literal[
    "generate_proposal",
    "generate_program",
    "generate_field_report",
    "compile_schedule",
    "workflow",
]


class ReviewSubmit(BaseModel):
    action: ReviewAction
    result: Dict[str, Any]


class ReviewRecord(BaseModel):
    review_id: str
    action: ReviewAction
    result: Dict[str, Any]
    state: Literal["pending", "approved", "rejected"]
    submitted_at: str
    decided_at: Optional[str] = None
    rejection_reason: Optional[str] = None


# ── Phase 18: Core Project State  [CORE] ──────────────────────────────────────

class CoreProjectState(BaseModel):
    project_id: str
    status: Literal["active", "pending_review", "reviewed"]
    summary: str
    review_required: bool
    pending_review_count: int
    review_count: int
    next_action: str
    created_at: str
    last_activity_at: str


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 23 DOMAIN MODELS
# Real client-domain entities derived from the S+A project template.
# Additive only — no existing models are modified.
# ══════════════════════════════════════════════════════════════════════════════

# ── Phase 23: Client  [DOMAIN] ────────────────────────────────────────────────

class ClientInput(BaseModel):
    project_id: str
    client_name: str
    home_address: Optional[str] = None
    home_phone: Optional[str] = None
    home_email: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None
    office_email: Optional[str] = None

    @field_validator("project_id", "client_name")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class ClientRecord(BaseModel):
    client_id: str
    project_id: str
    client_name: str
    home_address: Optional[str] = None
    home_phone: Optional[str] = None
    home_email: Optional[str] = None
    office_address: Optional[str] = None
    office_phone: Optional[str] = None
    office_email: Optional[str] = None
    created_at: str


# ── Phase 23: Property  [DOMAIN] ──────────────────────────────────────────────

class PropertyInput(BaseModel):
    project_id: str
    address: str
    town: Optional[str] = None
    map: Optional[str] = None
    lot: Optional[str] = None
    zoning_district: Optional[str] = None
    setback_front_ft: Optional[float] = None
    setback_side_ft: Optional[float] = None
    setback_rear_ft: Optional[float] = None
    bedroom_count: Optional[int] = None
    sf_existing_total: Optional[float] = None
    sf_new_total: Optional[float] = None
    total_project_cost: Optional[float] = None

    @field_validator("project_id", "address")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class PropertyRecord(BaseModel):
    property_id: str
    project_id: str
    address: str
    town: Optional[str] = None
    map: Optional[str] = None
    lot: Optional[str] = None
    zoning_district: Optional[str] = None
    setback_front_ft: Optional[float] = None
    setback_side_ft: Optional[float] = None
    setback_rear_ft: Optional[float] = None
    bedroom_count: Optional[int] = None
    sf_existing_total: Optional[float] = None
    sf_new_total: Optional[float] = None
    total_project_cost: Optional[float] = None
    created_at: str


# ── Phase 23: ReviewingBoard  [DOMAIN] ────────────────────────────────────────

BoardName = Literal[
    "ZBA",
    "conservation_commission",
    "planning_board",
    "board_of_health",
    "site_review",
    "historical_district",
    "mv_commission",
    "building_dept",
]

BoardStatus = Literal["not_required", "pending", "granted", "denied"]


class ReviewingBoardInput(BaseModel):
    project_id: str
    board_name: BoardName
    required: bool = False
    application_date: Optional[str] = None
    status: BoardStatus = "not_required"
    granted_denied_date: Optional[str] = None
    recorded_date: Optional[str] = None
    book: Optional[str] = None
    page: Optional[str] = None

    @field_validator("project_id")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class ReviewingBoardRecord(BaseModel):
    board_id: str
    project_id: str
    board_name: BoardName
    required: bool
    application_date: Optional[str] = None
    status: BoardStatus
    granted_denied_date: Optional[str] = None
    recorded_date: Optional[str] = None
    book: Optional[str] = None
    page: Optional[str] = None
    created_at: str
    updated_at: str


# ── Phase 23: MeetingMinute  [DOMAIN] ─────────────────────────────────────────

MeetingType = Literal["OAC", "design_review", "pre_construction", "closeout", "other"]


class ActionItem(BaseModel):
    description: str
    responsible_party: str
    due_date: Optional[str] = None
    status: Literal["open", "closed"] = "open"

    @field_validator("description", "responsible_party")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v


class MeetingMinuteInput(BaseModel):
    project_id: str
    meeting_date: str
    meeting_type: MeetingType
    location: Optional[str] = None
    attendees: List[str]
    agenda_items: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    next_meeting_date: Optional[str] = None

    @field_validator("project_id", "meeting_date")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v

    @field_validator("attendees")
    @classmethod
    def must_have_at_least_one(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("attendees must contain at least one entry")
        return v


class MeetingMinuteRecord(BaseModel):
    minute_id: str
    project_id: str
    meeting_date: str
    meeting_type: MeetingType
    location: Optional[str] = None
    attendees: List[str]
    agenda_items: List[str]
    action_items: List[ActionItem]
    next_meeting_date: Optional[str] = None
    created_at: str


# ── Phase 23: Directive  [DOMAIN] ─────────────────────────────────────────────

class DirectiveInput(BaseModel):
    project_id: str
    directive_number: int
    date: str
    description: str
    trade: Optional[str] = None
    drawing_references: List[str] = Field(default_factory=list)
    estimated_cost_impact: Optional[float] = None

    @field_validator("project_id", "date", "description")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must be non-empty")
        return v

    @field_validator("directive_number")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("directive_number must be at least 1")
        return v


class DirectiveRecord(BaseModel):
    directive_id: str
    project_id: str
    directive_number: int
    date: str
    description: str
    trade: Optional[str] = None
    drawing_references: List[str]
    estimated_cost_impact: Optional[float] = None
    created_at: str
