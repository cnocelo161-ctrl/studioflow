import fcntl
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path: Path, exclusive: bool = False):
    """Advisory file lock using a companion .lock file.

    exclusive=True  — LOCK_EX, for the full write path (read-modify-write-replace)
    exclusive=False — LOCK_SH, for reads

    A companion file (path + ".lock") is created if it does not exist.
    Locks are released automatically when the file descriptor is closed.
    """
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    with open(lock_path, "a") as lf:
        fcntl.flock(lf.fileno(), mode)
        try:
            yield
        finally:
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
