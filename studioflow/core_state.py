from typing import List

from models import CoreProjectState, ProjectRecord, ReviewRecord


def derive_core_state(
    project: ProjectRecord,
    reviews: List[ReviewRecord],
) -> CoreProjectState:
    """Derive generic project state from a ProjectRecord and its linked reviews.

    Expected to succeed for valid ProjectRecord and ReviewRecord objects produced
    by the current system. If schema drift occurs later, this is the single place
    to update the derivation logic.
    """
    pending = [r for r in reviews if r.state == "pending"]

    if pending:
        status = "pending_review"
    elif reviews:
        status = "reviewed"
    else:
        status = "active"

    pending_count = len(pending)
    review_count = len(reviews)

    summary = f"{project.project_type} — {project.client_name}, {project.property_address}"

    if pending_count > 0:
        next_action = f"{pending_count} review(s) pending decision"
    elif review_count > 0:
        next_action = "All reviews complete"
    else:
        next_action = "No reviews submitted"

    # max() over ISO strings is valid here only because all timestamps are
    # normalized UTC ISO 8601 strings produced by the current system (_now()).
    # Lexicographic ordering of UTC ISO 8601 strings is equivalent to
    # chronological ordering.
    timestamps = [project.created_at]
    for r in reviews:
        timestamps.append(r.submitted_at)
        if r.decided_at:
            timestamps.append(r.decided_at)
    last_activity_at = max(timestamps)

    return CoreProjectState(
        project_id=project.project_id,
        status=status,
        summary=summary,
        review_required=pending_count > 0,
        pending_review_count=pending_count,
        review_count=review_count,
        next_action=next_action,
        created_at=project.created_at,
        last_activity_at=last_activity_at,
    )
