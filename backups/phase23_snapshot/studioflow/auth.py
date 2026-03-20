import os
import sys

from flask import Flask, Response, request
from werkzeug.security import check_password_hash

# Read credentials once at import time.
# Validation logic lives here — config.py is passive.
_AUTH_USER = os.environ.get("STUDIOFLOW_AUTH_USER", "").strip()
_AUTH_PASSWORD_HASH = os.environ.get("STUDIOFLOW_AUTH_PASSWORD_HASH", "").strip()

_both_set = bool(_AUTH_USER) and bool(_AUTH_PASSWORD_HASH)
_neither_set = not _AUTH_USER and not _AUTH_PASSWORD_HASH

if not _both_set and not _neither_set:
    raise RuntimeError(
        "StudioFlow auth misconfiguration: "
        "STUDIOFLOW_AUTH_USER and STUDIOFLOW_AUTH_PASSWORD_HASH "
        "must both be set or both be unset."
    )

AUTH_ENABLED: bool = _both_set

if not AUTH_ENABLED:
    print(
        "WARNING: StudioFlow: auth is DISABLED — "
        "set STUDIOFLOW_AUTH_USER + STUDIOFLOW_AUTH_PASSWORD_HASH to enable.",
        file=sys.stderr,
    )


def _check_credentials(username: str, password: str) -> bool:
    if not AUTH_ENABLED:
        return True
    return username == _AUTH_USER and check_password_hash(_AUTH_PASSWORD_HASH, password)


def _unauthorized() -> Response:
    return Response(
        "Unauthorized",
        401,
        {"WWW-Authenticate": 'Basic realm="StudioFlow"'},
    )


def register(app: Flask) -> None:
    """Register the before_request auth hook on the Flask app."""

    @app.before_request
    def require_auth():
        if not AUTH_ENABLED:
            return None
        # /health is exempt
        if request.path == "/health":
            return None
        credentials = request.authorization
        if not credentials or not _check_credentials(credentials.username, credentials.password):
            return _unauthorized()
        return None
