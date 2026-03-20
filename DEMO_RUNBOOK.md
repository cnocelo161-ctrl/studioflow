> **NOTE:**
> For real client sessions and deployment, use **PILOT_RUNBOOK.md**.
> This document is for development and demo purposes only.

# StudioFlow Demo Runbook

## Environment Setup

```bash
cd openclaw
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Verify activation:**
```bash
which python
# Expected: .../openclaw/.venv/bin/python
```

> If this does not point to `.venv`, STOP and fix environment before proceeding.

## Run All Tests

```bash
cd openclaw
source .venv/bin/activate
python studioflow/run_tests.py
```

## Start the Server

```bash
cd openclaw
./start.sh
```

Runs on `http://127.0.0.1:5001/ui/` by default (daemonized via Gunicorn).

Override port: `STUDIOFLOW_PORT=8080 ./start.sh`

LAN access (expose to local network): `STUDIOFLOW_HOST=0.0.0.0 ./start.sh`

## Stop the Server

```bash
cd openclaw
./stop.sh
```

## Enabling Auth

By default auth is disabled (safe for single-operator local use with no network exposure).
To enable, generate a password hash and set both env vars before starting:

```bash
# Generate hash
.venv/bin/python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"

# Set env vars (add to your shell profile or .env loader)
export STUDIOFLOW_AUTH_USER=admin
export STUDIOFLOW_AUTH_PASSWORD_HASH=pbkdf2:sha256:...   # output from above

./start.sh
```

Both vars must be set or both must be blank — a partial configuration will cause a startup error.

When auth is enabled, all routes except `/health` require HTTP Basic Auth credentials.
Browsers prompt once per session; `curl` users pass `-u admin:yourpassword`.

## Health Check

```bash
curl http://localhost:5001/health
# {"status": "ok"}
```

## Demo Commands

**Generate a program (orchestrate):**
```bash
curl -s -X POST http://localhost:5001/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_program",
    "payload": {
      "project_id": "00000000-0000-0000-0000-000000000001",
      "spaces": [
        {
          "name": "Living Room",
          "level": "First Floor",
          "width_ft": 18.0,
          "length_ft": 22.0,
          "sf": 396.0,
          "requirements": [],
          "adjacencies": []
        }
      ]
    }
  }' | python -m json.tool
```

**Run full workflow:**
```bash
curl -s -X POST http://localhost:5001/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_intake": {
      "client_name": "Demo Client",
      "property_address": "1 Demo Lane, Edgartown, MA",
      "map": "01",
      "lot": "01",
      "project_type": "New Construction",
      "scope_phases": ["pre_design", "SD", "DD"],
      "billing_mode": "hourly"
    },
    "program_payload": {
      "spaces": [
        {
          "name": "Living Room",
          "level": "First Floor",
          "width_ft": 18.0,
          "length_ft": 22.0,
          "sf": 396.0,
          "requirements": [],
          "adjacencies": []
        }
      ]
    },
    "field_report_payload": {
      "visit_date": "2026-03-19",
      "visit_time": "10:00 AM",
      "weather": "Clear",
      "approximate_temp_f": 52.0,
      "phase": "CA",
      "work_in_progress": "Framing",
      "parties_present": ["GC"],
      "transmitted_to": ["Client"],
      "observations": ["On track"],
      "action_required": [],
      "old_items": [],
      "new_items": [],
      "site_photos": []
    },
    "schedule_payload": {
      "finish_entries": [
        {
          "space_name": "Living Room",
          "level": "First Floor",
          "flooring": "Oak",
          "tile": null,
          "paint_colors": "White"
        }
      ],
      "fixture_entries": []
    }
  }' | python -m json.tool
```

## Pre-Demo Checklist

- [ ] venv is active (`which python` points inside `.venv/`)
- [ ] dependencies installed (`pip install -r requirements.txt`)
- [ ] no process on port 5001 (`lsof -i :5001`)
- [ ] all tests green (`python studioflow/run_tests.py`)
- [ ] server started (`./start.sh`)
- [ ] health check passes (`curl http://127.0.0.1:5001/health`)

---

# Fallback (if activation fails)

Emergency fallback — bypasses activation issues:

```bash
./.venv/bin/python studioflow/run_tests.py
```
