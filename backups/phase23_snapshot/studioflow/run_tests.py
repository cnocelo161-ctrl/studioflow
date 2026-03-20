import subprocess
import sys
from pathlib import Path

STUDIOFLOW_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STUDIOFLOW_DIR.parent

test_files = sorted(STUDIOFLOW_DIR.glob("test_phase*.py"))

if __name__ == "__main__":
    passed, failed = [], []

    for f in test_files:
        result = subprocess.run(
            [sys.executable, str(f)],
            cwd=STUDIOFLOW_DIR,
        )
        if result.returncode == 0:
            passed.append(f.name)
        else:
            failed.append(f.name)

    print()
    print(f"Passed: {len(passed)}/{len(passed) + len(failed)}")
    for name in passed:
        print(f"  OK  {name}")
    for name in failed:
        print(f"  FAIL  {name}")

    if failed:
        sys.exit(1)
