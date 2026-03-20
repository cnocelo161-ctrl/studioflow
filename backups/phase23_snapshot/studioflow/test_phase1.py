from pydantic import ValidationError

from models import Phase1IntakeInput
from proposal import PHASE_ORDER, generate_proposal

# TEST INPUT — not real workflow data. Structurally valid minimal fixture only.
TEST_INTAKE = {
    "client_name": "[TEST CLIENT]",
    "property_address": "[TEST ADDRESS]",
    "map": "00",
    "lot": "00",
    "project_type": "[TEST PROJECT TYPE]",
    "scope_phases": ["pre_design", "SD", "DD", "CD", "contract", "CA"],
    "billing_mode": "hybrid",
    "probable_cost": 100000,
}
# probable_cost=100000 → fixed_fee_total assertion: == 12000.0

intake = Phase1IntakeInput(**TEST_INTAKE)
proposal = generate_proposal(intake)

assert proposal.document_ready is True
assert len(proposal.scope_of_services) == 6
assert [s.phase_token for s in proposal.scope_of_services] == list(PHASE_ORDER)
assert proposal.scope_of_services[0].billing_type == "hourly"   # pre_design, hybrid
assert proposal.scope_of_services[1].billing_type == "hourly"   # SD, hybrid
assert proposal.scope_of_services[2].billing_type == "fixed_fee"  # DD, hybrid
assert proposal.compensation.fixed_fee_total == 12000.0
assert proposal.compensation.fixed_fee_percent == 0.12
assert proposal.compensation.hourly_rates.founding_principal == 225.0
assert proposal.compensation.hourly_rates.project_administration == 125.0
assert proposal.compensation.hourly_phases == ["pre_design", "SD"]
assert proposal.compensation.fixed_fee_phases == ["DD", "CD", "contract", "CA"]
assert proposal.proposal_id  # valid non-empty string
assert "+00:00" in proposal.generated_at or "Z" in proposal.generated_at
assert proposal.scope_of_services[0].phase_code == "1.1"

print("All passing assertions passed.")

# TEST: validation must reject hybrid mode + fixed-fee phases + no probable_cost
bad_intake = {
    "client_name": "[TEST CLIENT]",
    "property_address": "[TEST ADDRESS]",
    "map": "00",
    "lot": "00",
    "project_type": "[TEST PROJECT TYPE]",
    "scope_phases": ["pre_design", "DD"],  # DD is a fixed-fee phase
    "billing_mode": "hybrid",
    "probable_cost": None,  # missing — must raise ValidationError
}

try:
    Phase1IntakeInput(**bad_intake)
    raise AssertionError("Expected ValidationError was not raised")
except ValidationError:
    pass  # correct — validation rejected invalid input

print("Failing test case passed (ValidationError correctly raised).")
print("All tests passed.")
