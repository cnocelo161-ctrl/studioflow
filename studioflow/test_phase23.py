import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import board_store
import client_store
import directive_store
import minute_store
import property_store
from interface import app

flask_client = app.test_client()


def fresh_tmp(suffix=".json"):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    os.unlink(path)
    return Path(path)


# ══════════════════════════════════════════════════════════════════════════════
# CLIENT
# ══════════════════════════════════════════════════════════════════════════════

VALID_CLIENT = {
    "project_id": "proj-001",
    "client_name": "Jane Doe",
    "home_address": "10 Oak Lane, Edgartown, MA",
    "home_email": "jane@example.com",
}

# ── Case 1: valid client create ───────────────────────────────────────────────

tmp = fresh_tmp()
with patch("client_store.CLIENT_PATH", tmp):
    client_store._store.clear()
    r = flask_client.post("/clients", json=VALID_CLIENT)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "client_id" in data
    assert data["client_name"] == "Jane Doe"
    assert data["project_id"] == "proj-001"
    assert "created_at" in data
tmp.unlink(missing_ok=True)
print("Case 1: POST /clients valid → 200 with ClientRecord.")

# ── Case 2: invalid client create (missing required fields) ──────────────────

tmp = fresh_tmp()
with patch("client_store.CLIENT_PATH", tmp):
    client_store._store.clear()
    r = flask_client.post("/clients", json={"home_address": "somewhere"})
    assert r.status_code == 422, r.get_json()
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 2: POST /clients invalid → 422.")

# ── Case 3: GET /clients/<client_id> returns record ──────────────────────────

tmp = fresh_tmp()
with patch("client_store.CLIENT_PATH", tmp):
    client_store._store.clear()
    r = flask_client.post("/clients", json=VALID_CLIENT)
    client_id = r.get_json()["client_id"]
    r2 = flask_client.get(f"/clients/{client_id}")
    assert r2.status_code == 200
    assert r2.get_json()["client_id"] == client_id
tmp.unlink(missing_ok=True)
print("Case 3: GET /clients/<client_id> returns record.")

# ── Case 4: GET /clients/<unknown_id> → 404 ──────────────────────────────────

tmp = fresh_tmp()
with patch("client_store.CLIENT_PATH", tmp):
    client_store._store.clear()
    r = flask_client.get("/clients/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 4: GET /clients/<unknown_id> → 404.")

# ── Case 5: GET /clients returns created records ─────────────────────────────

tmp = fresh_tmp()
with patch("client_store.CLIENT_PATH", tmp):
    client_store._store.clear()
    flask_client.post("/clients", json=VALID_CLIENT)
    r = flask_client.get("/clients")
    assert r.status_code == 200
    assert len(r.get_json()["clients"]) == 1
tmp.unlink(missing_ok=True)
print("Case 5: GET /clients returns created records.")


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTY
# ══════════════════════════════════════════════════════════════════════════════

VALID_PROPERTY = {
    "project_id": "proj-001",
    "address": "10 Oak Lane, Edgartown, MA",
    "town": "Edgartown",
    "zoning_district": "R-10",
    "sf_existing_total": 1800.0,
}

# ── Case 6: valid property create ────────────────────────────────────────────

tmp = fresh_tmp()
with patch("property_store.PROPERTY_PATH", tmp):
    property_store._store.clear()
    r = flask_client.post("/properties", json=VALID_PROPERTY)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "property_id" in data
    assert data["address"] == "10 Oak Lane, Edgartown, MA"
    assert "created_at" in data
tmp.unlink(missing_ok=True)
print("Case 6: POST /properties valid → 200 with PropertyRecord.")

# ── Case 7: invalid property create ──────────────────────────────────────────

tmp = fresh_tmp()
with patch("property_store.PROPERTY_PATH", tmp):
    property_store._store.clear()
    r = flask_client.post("/properties", json={"town": "Edgartown"})
    assert r.status_code == 422
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 7: POST /properties invalid → 422.")

# ── Case 8: GET /properties/<property_id> returns record ─────────────────────

tmp = fresh_tmp()
with patch("property_store.PROPERTY_PATH", tmp):
    property_store._store.clear()
    r = flask_client.post("/properties", json=VALID_PROPERTY)
    property_id = r.get_json()["property_id"]
    r2 = flask_client.get(f"/properties/{property_id}")
    assert r2.status_code == 200
    assert r2.get_json()["property_id"] == property_id
tmp.unlink(missing_ok=True)
print("Case 8: GET /properties/<property_id> returns record.")

# ── Case 9: GET /properties/<unknown_id> → 404 ───────────────────────────────

tmp = fresh_tmp()
with patch("property_store.PROPERTY_PATH", tmp):
    property_store._store.clear()
    r = flask_client.get("/properties/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 9: GET /properties/<unknown_id> → 404.")

# ── Case 10: GET /properties returns created records ─────────────────────────

tmp = fresh_tmp()
with patch("property_store.PROPERTY_PATH", tmp):
    property_store._store.clear()
    flask_client.post("/properties", json=VALID_PROPERTY)
    r = flask_client.get("/properties")
    assert r.status_code == 200
    assert len(r.get_json()["properties"]) == 1
tmp.unlink(missing_ok=True)
print("Case 10: GET /properties returns created records.")


# ══════════════════════════════════════════════════════════════════════════════
# REVIEWING BOARD
# ══════════════════════════════════════════════════════════════════════════════

VALID_BOARD = {
    "project_id": "proj-001",
    "board_name": "mv_commission",
    "required": True,
    "status": "pending",
    "application_date": "2026-02-01",
}

# ── Case 11: valid board create ───────────────────────────────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    r = flask_client.post("/boards", json=VALID_BOARD)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "board_id" in data
    assert data["board_name"] == "mv_commission"
    assert data["status"] == "pending"
    assert "created_at" in data
    assert "updated_at" in data
tmp.unlink(missing_ok=True)
print("Case 11: POST /boards valid → 200 with ReviewingBoardRecord.")

# ── Case 12: board create has created_at == updated_at ───────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    r = flask_client.post("/boards", json=VALID_BOARD)
    data = r.get_json()
    assert data["created_at"] == data["updated_at"]
tmp.unlink(missing_ok=True)
print("Case 12: board created_at == updated_at on creation.")

# ── Case 13: invalid board create (bad board_name) ───────────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    r = flask_client.post("/boards", json={"project_id": "proj-001", "board_name": "not_a_board"})
    assert r.status_code == 422
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 13: POST /boards invalid board_name → 422.")

# ── Case 14: GET /boards/<board_id> returns record ───────────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    r = flask_client.post("/boards", json=VALID_BOARD)
    board_id = r.get_json()["board_id"]
    r2 = flask_client.get(f"/boards/{board_id}")
    assert r2.status_code == 200
    assert r2.get_json()["board_id"] == board_id
tmp.unlink(missing_ok=True)
print("Case 14: GET /boards/<board_id> returns record.")

# ── Case 15: GET /boards/<unknown_id> → 404 ──────────────────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    r = flask_client.get("/boards/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 15: GET /boards/<unknown_id> → 404.")

# ── Case 16: GET /boards returns created records ─────────────────────────────

tmp = fresh_tmp()
with patch("board_store.BOARD_PATH", tmp):
    board_store._store.clear()
    flask_client.post("/boards", json=VALID_BOARD)
    r = flask_client.get("/boards")
    assert r.status_code == 200
    assert len(r.get_json()["boards"]) == 1
tmp.unlink(missing_ok=True)
print("Case 16: GET /boards returns created records.")


# ══════════════════════════════════════════════════════════════════════════════
# MEETING MINUTE
# ══════════════════════════════════════════════════════════════════════════════

VALID_MINUTE = {
    "project_id": "proj-001",
    "meeting_date": "2026-03-10",
    "meeting_type": "OAC",
    "attendees": ["Architect", "Owner"],
    "agenda_items": ["Review submittals"],
    "action_items": [
        {
            "description": "Submit RFI-12",
            "responsible_party": "Contractor",
            "due_date": "2026-03-17",
            "status": "open",
        }
    ],
}

# ── Case 17: valid minute create ─────────────────────────────────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    r = flask_client.post("/minutes", json=VALID_MINUTE)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "minute_id" in data
    assert data["meeting_type"] == "OAC"
    assert len(data["action_items"]) == 1
    assert "created_at" in data
tmp.unlink(missing_ok=True)
print("Case 17: POST /minutes valid → 200 with MeetingMinuteRecord.")

# ── Case 18: minute allows empty agenda_items and action_items ────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    r = flask_client.post("/minutes", json={
        "project_id": "proj-001",
        "meeting_date": "2026-03-10",
        "meeting_type": "other",
        "attendees": ["Architect"],
    })
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["agenda_items"] == []
    assert data["action_items"] == []
tmp.unlink(missing_ok=True)
print("Case 18: POST /minutes with empty agenda_items and action_items → 200.")

# ── Case 19: invalid minute create (no attendees) ────────────────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    r = flask_client.post("/minutes", json={
        "project_id": "proj-001",
        "meeting_date": "2026-03-10",
        "meeting_type": "OAC",
        "attendees": [],
    })
    assert r.status_code == 422
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 19: POST /minutes no attendees → 422.")

# ── Case 20: GET /minutes/<minute_id> returns record ─────────────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    r = flask_client.post("/minutes", json=VALID_MINUTE)
    minute_id = r.get_json()["minute_id"]
    r2 = flask_client.get(f"/minutes/{minute_id}")
    assert r2.status_code == 200
    assert r2.get_json()["minute_id"] == minute_id
tmp.unlink(missing_ok=True)
print("Case 20: GET /minutes/<minute_id> returns record.")

# ── Case 21: GET /minutes/<unknown_id> → 404 ─────────────────────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    r = flask_client.get("/minutes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 21: GET /minutes/<unknown_id> → 404.")

# ── Case 22: GET /minutes returns created records ────────────────────────────

tmp = fresh_tmp()
with patch("minute_store.MINUTE_PATH", tmp):
    minute_store._store.clear()
    flask_client.post("/minutes", json=VALID_MINUTE)
    r = flask_client.get("/minutes")
    assert r.status_code == 200
    assert len(r.get_json()["minutes"]) == 1
tmp.unlink(missing_ok=True)
print("Case 22: GET /minutes returns created records.")


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTIVE
# ══════════════════════════════════════════════════════════════════════════════

VALID_DIRECTIVE = {
    "project_id": "proj-001",
    "directive_number": 1,
    "date": "2026-03-15",
    "description": "Add blocking at stair header per RFI-07.",
    "trade": "Framing",
    "drawing_references": ["A-201"],
    "estimated_cost_impact": 850.0,
}

# ── Case 23: valid directive create ──────────────────────────────────────────

tmp = fresh_tmp()
with patch("directive_store.DIRECTIVE_PATH", tmp):
    directive_store._store.clear()
    r = flask_client.post("/directives", json=VALID_DIRECTIVE)
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert "directive_id" in data
    assert data["directive_number"] == 1
    assert data["trade"] == "Framing"
    assert "created_at" in data
tmp.unlink(missing_ok=True)
print("Case 23: POST /directives valid → 200 with DirectiveRecord.")

# ── Case 24: invalid directive create (directive_number = 0) ─────────────────

tmp = fresh_tmp()
with patch("directive_store.DIRECTIVE_PATH", tmp):
    directive_store._store.clear()
    bad = {**VALID_DIRECTIVE, "directive_number": 0}
    r = flask_client.post("/directives", json=bad)
    assert r.status_code == 422
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 24: POST /directives directive_number=0 → 422.")

# ── Case 25: GET /directives/<directive_id> returns record ───────────────────

tmp = fresh_tmp()
with patch("directive_store.DIRECTIVE_PATH", tmp):
    directive_store._store.clear()
    r = flask_client.post("/directives", json=VALID_DIRECTIVE)
    directive_id = r.get_json()["directive_id"]
    r2 = flask_client.get(f"/directives/{directive_id}")
    assert r2.status_code == 200
    assert r2.get_json()["directive_id"] == directive_id
tmp.unlink(missing_ok=True)
print("Case 25: GET /directives/<directive_id> returns record.")

# ── Case 26: GET /directives/<unknown_id> → 404 ──────────────────────────────

tmp = fresh_tmp()
with patch("directive_store.DIRECTIVE_PATH", tmp):
    directive_store._store.clear()
    r = flask_client.get("/directives/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert "detail" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 26: GET /directives/<unknown_id> → 404.")

# ── Case 27: GET /directives returns created records ─────────────────────────

tmp = fresh_tmp()
with patch("directive_store.DIRECTIVE_PATH", tmp):
    directive_store._store.clear()
    flask_client.post("/directives", json=VALID_DIRECTIVE)
    r = flask_client.get("/directives")
    assert r.status_code == 200
    assert len(r.get_json()["directives"]) == 1
tmp.unlink(missing_ok=True)
print("Case 27: GET /directives returns created records.")


# ══════════════════════════════════════════════════════════════════════════════
# NON-REGRESSION
# ══════════════════════════════════════════════════════════════════════════════

# ── Case 28: GET /health still returns 200 ───────────────────────────────────

r = flask_client.get("/health")
assert r.status_code == 200
assert r.get_json()["status"] == "ok"
print("Case 28: GET /health → 200 (non-regression).")

# ── Case 29: GET /projects still returns 200 ─────────────────────────────────

import project_store
tmp = fresh_tmp()
with patch("project_store.PROJECT_PATH", tmp):
    project_store._store.clear()
    r = flask_client.get("/projects")
    assert r.status_code == 200
    assert "projects" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 29: GET /projects → 200 (non-regression).")

# ── Case 30: GET /reviews still returns 200 ──────────────────────────────────

import review_store
tmp = fresh_tmp()
with patch("review_store.REVIEW_PATH", tmp):
    review_store._store.clear()
    r = flask_client.get("/reviews")
    assert r.status_code == 200
    assert "reviews" in r.get_json()
tmp.unlink(missing_ok=True)
print("Case 30: GET /reviews → 200 (non-regression).")

print("All Phase 23 tests passed.")
