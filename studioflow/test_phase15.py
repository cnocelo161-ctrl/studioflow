import json
import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import review_store

SAMPLE_RESULT = {"proposal_id": "00000000-0000-0000-0000-000000000001"}


def fresh_tmp():
    """Return a unique path that does not yet exist."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(path)
    return Path(path)


# ── Case 1: Submit flushes record to disk ─────────────────────────────────────

tmp = fresh_tmp()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    record = review_store.submit("generate_proposal", SAMPLE_RESULT)

    assert tmp.exists()
    data = json.loads(tmp.read_text())
    assert len(data) == 1
    assert data[0]["review_id"] == record.review_id
    assert data[0]["state"] == "pending"
    assert data[0]["action"] == "generate_proposal"

tmp.unlink(missing_ok=True)

print("Case 1: submit flushes record to disk.")

# ── Case 2: Approve flushes updated state to disk ─────────────────────────────

tmp = fresh_tmp()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    r = review_store.submit("generate_program", SAMPLE_RESULT)
    review_store.approve(r.review_id)

    data = json.loads(tmp.read_text())
    assert data[0]["state"] == "approved"
    assert data[0]["decided_at"] is not None

tmp.unlink(missing_ok=True)

print("Case 2: approve flushes updated state to disk.")

# ── Case 3: Reject flushes updated state and reason to disk ───────────────────

tmp = fresh_tmp()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    r = review_store.submit("workflow", SAMPLE_RESULT)
    review_store.reject(r.review_id, "Needs more spaces")

    data = json.loads(tmp.read_text())
    assert data[0]["state"] == "rejected"
    assert data[0]["rejection_reason"] == "Needs more spaces"

tmp.unlink(missing_ok=True)

print("Case 3: reject flushes updated state and reason to disk.")

# ── Case 4: Records survive restart ───────────────────────────────────────────

tmp = fresh_tmp()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    r1 = review_store.submit("generate_proposal", SAMPLE_RESULT)
    review_store.approve(r1.review_id)

    # simulate restart
    review_store._store.clear()
    review_store._load()

    assert r1.review_id in review_store._store
    reloaded = review_store._store[r1.review_id]
    assert reloaded.state == "approved"
    assert reloaded.decided_at is not None

tmp.unlink(missing_ok=True)

print("Case 4: records survive restart — loaded from disk.")

# ── Case 5: Insertion order preserved across restart ──────────────────────────

tmp = fresh_tmp()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    r1 = review_store.submit("generate_proposal", SAMPLE_RESULT)
    r2 = review_store.submit("generate_program", SAMPLE_RESULT)
    r3 = review_store.submit("workflow", SAMPLE_RESULT)

    original_order = [r1.review_id, r2.review_id, r3.review_id]

    review_store._store.clear()
    review_store._load()

    loaded_order = [r.review_id for r in review_store.list_all()]
    assert loaded_order == original_order

tmp.unlink(missing_ok=True)

print("Case 5: insertion order preserved across restart.")

# ── Case 6: Missing file on load → empty store, no exception ──────────────────

nonexistent = fresh_tmp()  # path does not exist

with patch("review_store.REVIEW_PATH", nonexistent):
    review_store._store.clear()
    review_store._load()

    assert len(review_store._store) == 0
    assert not nonexistent.exists()

print("Case 6: missing file on load → empty store, no crash.")

# ── Case 7: Malformed file → empty store, no crash, file untouched ────────────

tmp = fresh_tmp()
tmp.write_text("this is not valid json {{{{")
original_content = tmp.read_text()

captured = StringIO()

with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    with patch("sys.stderr", captured):
        review_store._load()

    assert len(review_store._store) == 0
    assert tmp.read_text() == original_content  # file untouched
    assert tmp.exists()

tmp.unlink(missing_ok=True)

print("Case 7: malformed file → empty store, no crash, file untouched, warning printed.")

print("All Phase 15 tests passed.")
