# StudioFlow — Pilot Runbook

This document is for operators running StudioFlow during a real client session.
Follow each section in order before and during the session.

---

## Pre-Session Checklist

Run this before every client session. Each item must be confirmed before opening
the browser.

### Step 1 — Run the automated preflight check

```bash
cd openclaw
./preflight.sh
```

The final line must read:

```
GO — system ready
```

If it reads `NO-GO`, fix the reported issues before continuing.
Do not skip this step.

### Step 2 — Take a backup

```bash
cd openclaw
./backup.sh
```

Confirm output ends with:

```
Backup complete: backups/YYYY-MM-DD_HHMMSS
```

Note the backup directory path in case you need to restore later.

### Step 3 — Confirm auth decision

**Option A — Auth disabled (machine is not network-accessible):**
No action needed. The preflight warning about auth being disabled is acceptable
if the machine is not exposed to a network. Note this decision.

**Option B — Auth enabled (recommended when others can reach the machine):**
Ensure `STUDIOFLOW_AUTH_USER` and `STUDIOFLOW_AUTH_PASSWORD_HASH` are set in
your environment before starting. See "Auth Setup" below if not already done.

### Step 4 — Start the server

```bash
cd openclaw
./start.sh
```

Confirm output ends with:

```
  Status : running
  URL    : http://127.0.0.1:5001/ui/
  PID    : <number>
```

### Step 5 — Health check

```bash
curl http://127.0.0.1:5001/health
```

Expected response: `{"status": "ok"}`

If you do not get this response, stop and see "Failure Scenarios" below.

### Step 6 — Open the UI

Open a browser and go to: `http://127.0.0.1:5001/ui/`

Confirm the dashboard loads. If auth is enabled, you will be prompted for
credentials. Enter them and confirm access.

You are now ready for the client session.

---

## Auth Setup

Do this once on the pilot machine before the first session.
Skip if you are running without auth (see Pre-Session Checklist, Step 3).

### Generate a password hash

```bash
cd openclaw
.venv/bin/python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword', method='pbkdf2:sha256'))"
```

Replace `yourpassword` with the actual password you want to use.
Copy the full output — it starts with `pbkdf2:sha256:`.

### Set the environment variables

Add these two lines to your shell profile (`~/.zshrc` or `~/.bash_profile`),
then reload your shell (`source ~/.zshrc`):

```bash
export STUDIOFLOW_AUTH_USER=admin
export STUDIOFLOW_AUTH_PASSWORD_HASH=pbkdf2:sha256:...   # paste full hash here
```

Both variables must be set or both must be blank.
Setting only one will cause a startup error.

### Verify auth is working

1. Start the server: `./start.sh`
2. Open `http://127.0.0.1:5001/ui/` in a browser
3. Confirm you are prompted for a username and password
4. Enter the credentials and confirm access
5. Run `curl http://127.0.0.1:5001/health` — must return 200 without credentials
6. Run `curl http://127.0.0.1:5001/projects` — must return 401 without credentials

---

## Deployment Drill

Run this sequence once on the pilot machine before the first real client session.
This confirms the full system works end-to-end.

1. Run `./preflight.sh` — must print `GO`
2. Run `./backup.sh` — confirm backup directory is created
3. Run `./start.sh` — note the PID
4. Run `curl http://127.0.0.1:5001/health` — must return `{"status": "ok"}`
5. Open `http://127.0.0.1:5001/ui/` — confirm dashboard loads
6. Go to Projects → New Project — fill out and submit the intake form
7. Confirm the project appears in the projects list with `Active` status
8. Open the project — confirm detail page loads with workflow output
9. Submit a review from the detail page
10. Confirm status changes to `Review Required` (amber badge)
11. Approve the review
12. Confirm status changes to `Reviewed` (green badge)
13. Run `./stop.sh` — confirm clean exit message
14. Confirm no `studioflow.pid` file remains in the `openclaw/` directory

If all 14 steps complete without error, the system is pilot-ready.

---

## Backup Procedure

Take a backup before every client session and after any session where new data
was created.

```bash
cd openclaw
./backup.sh
```

Backups are saved to `openclaw/backups/YYYY-MM-DD_HHMMSS/`.
Each backup contains `projects.json` and `reviews.json`.
The server does not need to be stopped to take a backup.

Note: because StudioFlow uses full-file atomic writes, each backup captures a
consistent full-file snapshot of whichever version of the data exists at the
moment the backup runs. This is acceptable for this system.

---

## Restore Procedure

Use this if data is lost or corrupted and you need to restore from a backup.

**The server must be stopped before restoring.**

1. Stop the server: `./stop.sh`
2. Identify the backup you want to restore from (`ls openclaw/backups/`)
3. Run the restore:

```bash
cd openclaw
./restore.sh backups/YYYY-MM-DD_HHMMSS
```

Confirm output ends with:

```
Restore complete from: ...
  Start the server: ./start.sh
```

4. Start the server: `./start.sh`
5. Open the UI and confirm the restored data appears

---

## Startup Procedure

```bash
cd openclaw
./start.sh
```

The server starts in the background (daemonized). It binds to `127.0.0.1:5001`
by default.

To use a different port:

```bash
STUDIOFLOW_PORT=5002 ./start.sh
```

To expose on the local network (use with auth enabled):

```bash
STUDIOFLOW_HOST=0.0.0.0 ./start.sh
```

---

## Shutdown Procedure

```bash
cd openclaw
./stop.sh
```

Confirm output: `StudioFlow stopped (was PID XXXXX)`

Take a post-session backup before shutting down if new data was created:

```bash
./backup.sh
./stop.sh
```

---

## Browser Workflow

This is the normal operator workflow during a client session.

### Create a project

1. Go to `http://127.0.0.1:5001/ui/`
2. Click **Projects** in the navigation
3. Click **+ New Project**
4. Fill in all required fields and submit
5. The new project appears in the list with `Active` status

### Review workflow output

1. Click a project in the list to open the detail page
2. The status strip shows current status and next action
3. Expand "Workflow Output (JSON)" to see the full generated output

### Submit a review

1. From the project detail page, use the review submission controls
2. After submitting, the project status changes to `Review Required`
3. The "Action Required" banner appears on the detail page

### Approve or reject a review

1. Open the project detail page
2. Find the review in the Reviews table
3. Click **Approve** or **Reject**
4. The status updates immediately

### Monitor pending reviews

1. Go to `http://127.0.0.1:5001/ui/reviews`
2. All pending reviews are listed here
3. Projects with pending reviews show an amber left border in the projects list

---

## Failure Scenarios

### Server does not start — port already in use

```
ERROR: Port 5001 is already in use (PID(s): XXXXX).
```

Find and stop the process using that port:

```bash
lsof -i TCP:5001 -sTCP:LISTEN
kill <PID>
```

Then retry `./start.sh`.

### Server does not start — already running

```
ERROR: StudioFlow is already running (PID XXXXX).
```

The server is already running. Open the UI directly, or stop it first with
`./stop.sh` if you need to restart.

### Server does not start — partial auth configuration

```
RuntimeError: StudioFlow auth misconfiguration
```

Both `STUDIOFLOW_AUTH_USER` and `STUDIOFLOW_AUTH_PASSWORD_HASH` must be set,
or both must be blank. Check your environment variables and retry.

### Browser shows "connection refused"

The server is not running. Start it:

```bash
cd openclaw
./start.sh
```

If `./start.sh` reports it is already running, check the health endpoint:

```bash
curl http://127.0.0.1:5001/health
```

### `./stop.sh` reports "studioflow.pid not found"

The server is not running (or it was stopped another way). No action needed.

### `./stop.sh` fails but server is still running

Find the gunicorn process manually and stop it:

```bash
ps aux | grep gunicorn
kill <PID>
```

Then remove the stale PID file if it exists:

```bash
rm openclaw/studioflow.pid
```

### Data appears missing after restart

The data files may be missing or empty. Check:

```bash
ls openclaw/studioflow/data/
```

If the files are absent or empty, restore from the most recent backup:

```bash
cd openclaw
./restore.sh backups/<most-recent-directory>
```

### Logs

Server logs are in `openclaw/logs/`:

- `access.log` — all HTTP requests
- `error.log` — server errors

```bash
tail -f openclaw/logs/error.log
```

---

## Post-Session Checklist

Complete these steps at the end of every client session.

- [ ] Take a final backup: `./backup.sh`
- [ ] Stop the server: `./stop.sh`
- [ ] Confirm no `studioflow.pid` file remains
- [ ] Note the backup directory path in your session notes
- [ ] If any data errors occurred, record them before closing
