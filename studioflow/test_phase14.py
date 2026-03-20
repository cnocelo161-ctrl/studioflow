from interface import app

client = app.test_client()

# ── Case 1: GET /ui/ returns 200 HTML ─────────────────────────────────────────

r = client.get("/ui/")
assert r.status_code == 200
assert "text/html" in r.content_type

print("Case 1: GET /ui/ returns 200 HTML.")

# ── Case 2: GET /ui/workflow returns 200 HTML ──────────────────────────────────

r = client.get("/ui/workflow")
assert r.status_code == 200
assert "text/html" in r.content_type

print("Case 2: GET /ui/workflow returns 200 HTML.")

# ── Case 3: GET /ui/reviews returns 200 HTML ──────────────────────────────────

r = client.get("/ui/reviews")
assert r.status_code == 200
assert "text/html" in r.content_type

print("Case 3: GET /ui/reviews returns 200 HTML.")

# ── Case 4: All UI routes are registered — none return 404 ────────────────────

for path in ["/ui/", "/ui/workflow", "/ui/reviews"]:
    r = client.get(path)
    assert r.status_code != 404, f"{path} returned 404"

print("Case 4: all UI routes registered and reachable.")

print("All Phase 14 tests passed.")
