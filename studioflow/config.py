import os
from pathlib import Path

_DEFAULT_LOG_PATH = Path(__file__).resolve().parent / "logs" / "audit.log"


def _bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes")


_host = os.environ.get("STUDIOFLOW_HOST", "").strip()
INTERFACE_HOST: str = _host if _host else "127.0.0.1"

_port = os.environ.get("STUDIOFLOW_PORT", "").strip()
INTERFACE_PORT: int = int(_port) if _port else 5001

_debug = os.environ.get("STUDIOFLOW_DEBUG", "").strip()
INTERFACE_DEBUG: bool = _bool(_debug) if _debug else False

_log = os.environ.get("STUDIOFLOW_LOG_PATH", "").strip()
if _log:
    _p = Path(_log)
    LOG_PATH: Path = _p if _p.is_absolute() else Path.cwd() / _p
else:
    LOG_PATH: Path = _DEFAULT_LOG_PATH

# Auth credentials — passive values only; validation lives in auth.py
AUTH_USER: str = os.environ.get("STUDIOFLOW_AUTH_USER", "").strip()
AUTH_PASSWORD_HASH: str = os.environ.get("STUDIOFLOW_AUTH_PASSWORD_HASH", "").strip()
