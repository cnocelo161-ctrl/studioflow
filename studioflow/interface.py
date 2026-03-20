import json
import time

from flask import Flask, request, jsonify
from pydantic import ValidationError

import auth
import board_store
import client_store
import directive_store
import minute_store
import project_store
import property_store
import review_store
from core_state import derive_core_state
from logger import log_entry, log_review_action
from models import (
    OrchestratorRequest,
    WorkflowInput,
    ReviewSubmit,
    ClientInput,
    PropertyInput,
    ReviewingBoardInput,
    MeetingMinuteInput,
    DirectiveInput,
)
from orchestrator import run
from ui import ui as ui_blueprint
from workflow import run_workflow

app = Flask(__name__)
app.register_blueprint(ui_blueprint)
auth.register(app)


@app.post("/orchestrate")
def orchestrate():
    t0 = time.monotonic()
    body = request.get_json(silent=True) or {}
    action = body.get("action") if isinstance(body, dict) else None
    status, error_type = None, None
    try:
        response = run(OrchestratorRequest(**body))
        status = 200
        return jsonify(response.model_dump()), 200
    except ValidationError as e:
        status, error_type = 422, "validation_error"
        return jsonify({"error": "validation_error", "status": 422, "detail": str(e), "errors": e.errors()}), 422
    except Exception as e:
        status, error_type = 500, "internal_error"
        return jsonify({"error": "internal_error", "status": 500, "detail": str(e)}), 500
    finally:
        log_entry(
            route="/orchestrate",
            action=action,
            outcome="success" if status == 200 else "error",
            status=status,
            error_type=error_type,
            duration_ms=round((time.monotonic() - t0) * 1000, 2),
        )


@app.post("/workflow")
def workflow():
    t0 = time.monotonic()
    body = request.get_json(silent=True) or {}
    status, error_type = None, None
    try:
        result = run_workflow(WorkflowInput(**body))
        status = 200
        return jsonify(result.model_dump()), 200
    except ValidationError as e:
        status, error_type = 422, "validation_error"
        return jsonify({"error": "validation_error", "status": 422, "detail": str(e), "errors": e.errors()}), 422
    except Exception as e:
        status, error_type = 500, "internal_error"
        return jsonify({"error": "internal_error", "status": 500, "detail": str(e)}), 500
    finally:
        log_entry(
            route="/workflow",
            action="workflow",
            outcome="success" if status == 200 else "error",
            status=status,
            error_type=error_type,
            duration_ms=round((time.monotonic() - t0) * 1000, 2),
        )


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/review")
def submit_review():
    body = request.get_json(silent=True) or {}
    try:
        req = ReviewSubmit(**body)
        record = review_store.submit(req.action, req.result)
        log_review_action(review_id=record.review_id, action=record.action, review_state="pending", rejection_reason=None)
        return jsonify(record.model_dump()), 200
    except ValidationError as e:
        return jsonify({"error": "validation_error", "status": 422, "detail": str(e), "errors": e.errors()}), 422


@app.get("/review/<review_id>")
def get_review(review_id):
    try:
        record = review_store.get(review_id)
        return jsonify(record.model_dump()), 200
    except KeyError:
        return jsonify({"error": "not_found", "status": 404, "detail": f"Review {review_id} not found"}), 404


@app.post("/review/<review_id>/approve")
def approve_review(review_id):
    try:
        record = review_store.approve(review_id)
        log_review_action(review_id=record.review_id, action=record.action, review_state="approved", rejection_reason=None)
        return jsonify(record.model_dump()), 200
    except KeyError:
        return jsonify({"error": "not_found", "status": 404, "detail": f"Review {review_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": "conflict", "status": 409, "detail": str(e)}), 409


@app.post("/review/<review_id>/reject")
def reject_review(review_id):
    body = request.get_json(silent=True) or {}
    reason = body.get("reason") if isinstance(body, dict) else None
    try:
        record = review_store.reject(review_id, reason)
        log_review_action(review_id=record.review_id, action=record.action, review_state="rejected", rejection_reason=record.rejection_reason)
        return jsonify(record.model_dump()), 200
    except KeyError:
        return jsonify({"error": "not_found", "status": 404, "detail": f"Review {review_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": "conflict", "status": 409, "detail": str(e)}), 409


@app.get("/reviews")
def list_reviews():
    records = review_store.list_all()
    return jsonify({"reviews": [r.model_dump() for r in records]}), 200


@app.post("/projects/run")
def projects_run():
    body = request.get_json(silent=True) or {}
    try:
        result = run_workflow(WorkflowInput(**body))
        record = project_store.save(result.model_dump())
        return jsonify(record.model_dump()), 200
    except ValidationError as e:
        return jsonify({"error": "validation_error", "status": 422, "detail": str(e), "errors": e.errors()}), 422
    except Exception as e:
        return jsonify({"error": "internal_error", "status": 500, "detail": str(e)}), 500


@app.get("/projects")
def list_projects():
    records = project_store.list_all()
    all_reviews = review_store.list_all()
    summaries = []
    for r in records:
        linked = [rv for rv in all_reviews if rv.result.get("project_id") == r.project_id]
        summaries.append({
            "project_id": r.project_id,
            "client_name": r.client_name,
            "property_address": r.property_address,
            "project_type": r.project_type,
            "created_at": r.created_at,
            "core": derive_core_state(r, linked).model_dump(),
        })
    return jsonify({"projects": summaries}), 200


@app.get("/projects/<project_id>")
def get_project(project_id):
    try:
        record = project_store.get(project_id)
        linked_reviews = [
            r for r in review_store.list_all()
            if r.result.get("project_id") == project_id
        ]
        data = record.model_dump()
        data["reviews"] = [r.model_dump() for r in linked_reviews]
        data["core"] = derive_core_state(record, linked_reviews).model_dump()
        return jsonify(data), 200
    except KeyError:
        return jsonify({"error": "not_found", "status": 404, "detail": f"Project {project_id} not found"}), 404


# ── Phase 23B: Client routes ──────────────────────────────────────────────────

@app.post("/clients")
def create_client():
    body = request.get_json(silent=True) or {}
    try:
        record = client_store.create(ClientInput(**body))
    except ValidationError as e:
        return jsonify({"detail": json.loads(e.json())}), 422
    return jsonify(record.model_dump()), 200


@app.get("/clients")
def list_clients():
    return jsonify({"clients": [r.model_dump() for r in client_store.list_all()]}), 200


@app.get("/clients/<client_id>")
def get_client(client_id):
    try:
        record = client_store.get(client_id)
    except KeyError:
        return jsonify({"detail": "Not found"}), 404
    return jsonify(record.model_dump()), 200


# ── Phase 23B: Property routes ────────────────────────────────────────────────

@app.post("/properties")
def create_property():
    body = request.get_json(silent=True) or {}
    try:
        record = property_store.create(PropertyInput(**body))
    except ValidationError as e:
        return jsonify({"detail": json.loads(e.json())}), 422
    return jsonify(record.model_dump()), 200


@app.get("/properties")
def list_properties():
    return jsonify({"properties": [r.model_dump() for r in property_store.list_all()]}), 200


@app.get("/properties/<property_id>")
def get_property(property_id):
    try:
        record = property_store.get(property_id)
    except KeyError:
        return jsonify({"detail": "Not found"}), 404
    return jsonify(record.model_dump()), 200


# ── Phase 23B: ReviewingBoard routes ─────────────────────────────────────────

@app.post("/boards")
def create_board():
    body = request.get_json(silent=True) or {}
    try:
        record = board_store.create(ReviewingBoardInput(**body))
    except ValidationError as e:
        return jsonify({"detail": json.loads(e.json())}), 422
    return jsonify(record.model_dump()), 200


@app.get("/boards")
def list_boards():
    return jsonify({"boards": [r.model_dump() for r in board_store.list_all()]}), 200


@app.get("/boards/<board_id>")
def get_board(board_id):
    try:
        record = board_store.get(board_id)
    except KeyError:
        return jsonify({"detail": "Not found"}), 404
    return jsonify(record.model_dump()), 200


# ── Phase 23B: MeetingMinute routes ──────────────────────────────────────────

@app.post("/minutes")
def create_minute():
    body = request.get_json(silent=True) or {}
    try:
        record = minute_store.create(MeetingMinuteInput(**body))
    except ValidationError as e:
        return jsonify({"detail": json.loads(e.json())}), 422
    return jsonify(record.model_dump()), 200


@app.get("/minutes")
def list_minutes():
    return jsonify({"minutes": [r.model_dump() for r in minute_store.list_all()]}), 200


@app.get("/minutes/<minute_id>")
def get_minute(minute_id):
    try:
        record = minute_store.get(minute_id)
    except KeyError:
        return jsonify({"detail": "Not found"}), 404
    return jsonify(record.model_dump()), 200


# ── Phase 23B: Directive routes ───────────────────────────────────────────────

@app.post("/directives")
def create_directive():
    body = request.get_json(silent=True) or {}
    try:
        record = directive_store.create(DirectiveInput(**body))
    except ValidationError as e:
        return jsonify({"detail": json.loads(e.json())}), 422
    return jsonify(record.model_dump()), 200


@app.get("/directives")
def list_directives():
    return jsonify({"directives": [r.model_dump() for r in directive_store.list_all()]}), 200


@app.get("/directives/<directive_id>")
def get_directive(directive_id):
    try:
        record = directive_store.get(directive_id)
    except KeyError:
        return jsonify({"detail": "Not found"}), 404
    return jsonify(record.model_dump()), 200


if __name__ == "__main__":
    from config import INTERFACE_PORT, INTERFACE_DEBUG
    app.run(debug=INTERFACE_DEBUG, port=INTERFACE_PORT)
