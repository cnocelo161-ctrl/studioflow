import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import review_store
from interface import app

client = app.test_client()

SAMPLE_RESULT = {
    "proposal_id": "00000000-0000-0000-0000-000000000001",
    "client_name": "Demo Client",
}

with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as rtmp:
    reviews_tmp = Path(rtmp.name)

with patch("review_store.REVIEW_PATH", reviews_tmp):
    review_store._store.clear()

    # ── Case 1: Submit a StudioFlow output ────────────────────────────────────────

    r = client.post("/review", json={"action": "generate_proposal", "result": SAMPLE_RESULT})
    assert r.status_code == 200
    data = r.get_json()
    assert data["state"] == "pending"
    assert data["action"] == "generate_proposal"
    assert data["result"] == SAMPLE_RESULT
    assert data["decided_at"] is None
    assert data["rejection_reason"] is None
    assert len(data["review_id"]) == 36  # UUID4
    review_id_1 = data["review_id"]

    print("Case 1: submit returns pending ReviewRecord.")

    # ── Case 2: Get by review_id ───────────────────────────────────────────────────

    r = client.get(f"/review/{review_id_1}")
    assert r.status_code == 200
    assert r.get_json() == data

    print("Case 2: GET /review/<id> returns exact record.")

    # ── Case 3: Approve ────────────────────────────────────────────────────────────

    r = client.post(f"/review/{review_id_1}/approve")
    assert r.status_code == 200
    data3 = r.get_json()
    assert data3["state"] == "approved"
    assert data3["decided_at"] is not None
    assert data3["rejection_reason"] is None

    print("Case 3: approve sets state=approved and decided_at.")

    # ── Case 4: Double-approve → 409 ──────────────────────────────────────────────

    r = client.post(f"/review/{review_id_1}/approve")
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"

    print("Case 4: double-approve returns 409.")

    # ── Case 5: Submit second, reject with reason ──────────────────────────────────

    r = client.post("/review", json={"action": "generate_program", "result": {"program_id": "abc"}})
    assert r.status_code == 200
    review_id_2 = r.get_json()["review_id"]

    r = client.post(f"/review/{review_id_2}/reject", json={"reason": "Needs more spaces"})
    assert r.status_code == 200
    data5 = r.get_json()
    assert data5["state"] == "rejected"
    assert data5["decided_at"] is not None
    assert data5["rejection_reason"] == "Needs more spaces"

    print("Case 5: reject with reason sets state=rejected and captures reason.")

    # ── Case 6: Double-reject → 409 ───────────────────────────────────────────────

    r = client.post(f"/review/{review_id_2}/reject", json={"reason": "Again"})
    assert r.status_code == 409
    assert r.get_json()["error"] == "conflict"

    print("Case 6: double-reject returns 409.")

    # ── Case 7: Unknown review_id → 404 ───────────────────────────────────────────

    r = client.get("/review/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.get_json()["error"] == "not_found"

    print("Case 7: unknown review_id returns 404.")

    # ── Case 8: List all — insertion order, count = 2 ─────────────────────────────

    r = client.get("/reviews")
    assert r.status_code == 200
    reviews = r.get_json()["reviews"]
    assert len(reviews) == 2
    assert reviews[0]["review_id"] == review_id_1
    assert reviews[1]["review_id"] == review_id_2

    print("Case 8: GET /reviews returns all records in insertion order.")

    # ── Case 9: Invalid action → 422 ──────────────────────────────────────────────

    r = client.post("/review", json={"action": "invalid_action", "result": {}})
    assert r.status_code == 422
    assert r.get_json()["error"] == "validation_error"

    print("Case 9: unknown action returns 422.")

    # ── Case 10: Audit log — submit/approve/reject log; get/list do not ───────────

    review_store._store.clear()

    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    with patch("logger.LOG_PATH", tmp_path):
        r = client.post("/review", json={"action": "compile_schedule", "result": {"schedule_id": "x"}})
        rid = r.get_json()["review_id"]
        client.post(f"/review/{rid}/approve")

        r2 = client.post("/review", json={"action": "workflow", "result": {"project_id": "y"}})
        rid2 = r2.get_json()["review_id"]
        client.post(f"/review/{rid2}/reject", json={"reason": "Not ready"})

        # reads — should not log
        client.get(f"/review/{rid}")
        client.get("/reviews")

    records = [json.loads(line) for line in tmp_path.read_text().strip().splitlines()]
    assert len(records) == 4  # submit, approve, submit, reject
    assert all(rec["event"] == "review_action" for rec in records)
    assert records[0]["review_state"] == "pending"
    assert records[1]["review_state"] == "approved"
    assert records[2]["review_state"] == "pending"
    assert records[3]["review_state"] == "rejected"
    assert records[3]["rejection_reason"] == "Not ready"

    tmp_path.unlink(missing_ok=True)

    print("Case 10: audit log records submit/approve/reject only; reads are unaudited.")

reviews_tmp.unlink(missing_ok=True)

print("All Phase 13 tests passed.")
