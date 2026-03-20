import json
import uuid
from datetime import datetime, timezone

from models import (
    ClientInfo,
    Compensation,
    HourlyRates,
    Phase1IntakeInput,
    PhaseService,
    ProposalOutput,
)

# Source provenance constants — documentation only, not used in logic
SOURCE_PRIMARY = "Proposal for Services 2025 PDF"
SOURCE_SECONDARY = [
    "Client Planning Timeline PDF",
    "Program of Spaces template PDF",
]

PHASE_ORDER = ("pre_design", "SD", "DD", "CD", "contract", "CA")

FIXED_FEE_NATIVE = {"DD", "CD", "contract", "CA"}

FIXED_FEE_PERCENT = 0.12

PHASE_METADATA = {
    "pre_design": {
        "phase_code": "1.1",
        "name": "Pre-Design",
        "native_billing": "hourly",
        "tasks": [
            "Inventory and analyze existing structures, amenities, and site features",
            "Create existing conditions drawings as required",
            "Prepare Zoning Analysis outlining all applicable Federal, State, and Local zoning and conservation restrictions, and building limitations",
            "Issue RFP for primary consultants: geotechnical, civil, as required",
            "Develop Preliminary Program of Spaces",
            "Review environmental goals",
            "Discuss primary consultants: Landscape Architect, Interior Designer",
            "Finalize Program of Spaces, review Budget, and Schedule",
        ],
    },
    "SD": {
        "phase_code": "1.2",
        "name": "Schematic Design",
        "native_billing": "hourly",
        "tasks": [
            "Prepare Schematic Design drawings, sketches, plans, elevations, sections, and models as required",
            "Issue RFP for Structural Engineer",
            "Acquire DWG and site information from Civil Engineers; develop Preliminary Site Plan",
            "Finalize primary consultants: Engineering, Landscape, Interiors",
            "Discuss secondary consultants: MEP, Solar, Lighting, AV",
            "Present SD set to client; may include models, images, textures",
            "Revise Schematic Design as necessary",
            "Work with contractor to develop Opinion of Probable Cost of Construction",
        ],
    },
    "DD": {
        "phase_code": "1.3",
        "name": "Design Development",
        "native_billing": "fixed_fee",
        "tasks": [
            "Prepare Outline Specification Manual listing finishes, preferred mechanical systems, construction methods and materials",
            "Create more detailed drawings including specific windows and doors, refinements to the exterior appearance, and development of Floor Plans and Elevations",
            "Review Design Development documents with client and revise as needed",
            "Coordinate and file for any necessary permitting (ZBA, ConComm); attend all required hearings",
            "Obtain Opinion of Probable Cost of Construction from a licensed contractor",
            "Perform Value Engineering as required: review Floor Plans, fixtures, and finishes to align Budget and Probable Cost",
        ],
    },
    "CD": {
        "phase_code": "1.4",
        "name": "Construction Documents",
        "native_billing": "fixed_fee",
        "tasks": [
            "Prepare comprehensive drawing set: Foundation Plan, Floor Plans, Building Sections, Assembly Details, Exterior Elevations, Interior Elevations, Door and Window Schedules",
            "Milestone reviews at 25%, 50%, 75%, and 90% completion with client",
            "Develop structural drawings with engineer through all CD milestones",
            "Develop grading plans with Landscape Architect",
            "Prepare Specification Manual including General Contractor responsibilities throughout the project and beyond, with a one-year warranty",
            "Finalize all Fixture and Finish Schedules: electrical and plumbing fixtures, tile, flooring, cabinets, hardware, appliances, paint colors",
        ],
    },
    "contract": {
        "phase_code": "1.5",
        "name": "Contract and Negotiation",
        "native_billing": "fixed_fee",
        "tasks": [
            "Issue Construction Documents to bidders",
            "Review bids and create Bid Analysis",
            "Perform further cost engineering as required",
            "Finalize and award contract",
        ],
    },
    "CA": {
        "phase_code": "1.6",
        "name": "Construction Administration",
        "native_billing": "fixed_fee",
        "tasks": [
            "Conduct periodic site visits to observe construction progress and answer questions from the contractor",
            "Take photos of construction progress and forward to client",
            "Review Applications for Payment based on progress and forward to client for payment",
            "Review and negotiate Requests for Change Orders prior to client approval",
            "Prepare and administer Punch List",
            "Review final reconciliation of contract and complete Project Closeout following final walk through with client and contractor",
        ],
    },
}


def _resolve_billing_type(phase_token: str, billing_mode: str) -> str:
    if billing_mode == "hourly":
        return "hourly"

    if billing_mode == "fixed_fee":
        return "fixed_fee"

    if billing_mode == "hybrid":
        return "fixed_fee" if phase_token in FIXED_FEE_NATIVE else "hourly"

    # defensive fail — should never happen if validation is correct
    raise ValueError(f"Unsupported billing_mode: {billing_mode}")


def generate_proposal(intake: Phase1IntakeInput) -> ProposalOutput:
    proposal_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    ordered_phases = [p for p in PHASE_ORDER if p in intake.scope_phases]

    scope_of_services = []
    hourly_phases = []
    fixed_fee_phases = []

    for token in ordered_phases:
        meta = PHASE_METADATA[token]
        billing_type = _resolve_billing_type(token, intake.billing_mode)
        scope_of_services.append(
            PhaseService(
                phase_code=meta["phase_code"],
                phase_token=token,
                name=meta["name"],
                billing_type=billing_type,
                tasks=meta["tasks"],
            )
        )
        if billing_type == "hourly":
            hourly_phases.append(token)
        else:
            fixed_fee_phases.append(token)

    fixed_fee_total = (
        round(intake.probable_cost * FIXED_FEE_PERCENT, 2)
        if fixed_fee_phases and intake.probable_cost is not None
        else None
    )

    compensation = Compensation(
        billing_mode=intake.billing_mode,
        hourly_phases=hourly_phases,
        fixed_fee_phases=fixed_fee_phases,
        hourly_rates=HourlyRates(),
        fixed_fee_percent=FIXED_FEE_PERCENT if fixed_fee_phases else None,
        probable_cost=intake.probable_cost,
        fixed_fee_total=fixed_fee_total,
    )

    client = ClientInfo(
        name=intake.client_name,
        property_address=intake.property_address,
        map=intake.map,
        lot=intake.lot,
    )

    return ProposalOutput(
        proposal_id=proposal_id,
        project_id=project_id,
        client=client,
        project_type=intake.project_type,
        scope_of_services=scope_of_services,
        compensation=compensation,
        document_ready=True,
        generated_at=generated_at,
    )


# SAMPLE INPUT — local CLI use only, not real workflow data
SAMPLE_INPUT = {
    "client_name": "[SAMPLE CLIENT]",
    "property_address": "[SAMPLE ADDRESS]",
    "map": "00",
    "lot": "00",
    "project_type": "[SAMPLE PROJECT TYPE]",
    "scope_phases": ["pre_design", "SD", "DD", "CD", "contract", "CA"],
    "billing_mode": "hybrid",
    "probable_cost": 100000,
}

if __name__ == "__main__":
    intake = Phase1IntakeInput(**SAMPLE_INPUT)
    proposal = generate_proposal(intake)
    print(json.dumps(proposal.model_dump(), indent=2))
