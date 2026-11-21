"""
Run the Report test scripts one after another, with one terminal command.

    python run_all.py                 run every repXXX_*.py file
    python run_all.py rep001 rep024   run only the files whose name starts with these

Each test runs in its own process (its own Chrome window), so one broken test
cannot stop the others. Output of every test is saved in logs/<test file>.log
and Allure 2 results are written to ../allure-results/ (or REPORT_ALLURE_RESULTS_DIR).
Keep the Excel file closed while this runs.
"""
import os
from pathlib import Path
import subprocess
import sys
import time

FOLDER = Path(__file__).resolve().parent
PROJECT_ROOT = FOLDER.parent
LOG_DIR = FOLDER / "logs"
TIMEOUT_SECONDS = 600  # give up on one test after 10 minutes


def find_tests(filters):
    """Return sorted repXXX_*.py test scripts, optionally filtered by filename prefix."""
    files = sorted(FOLDER.glob("rep[0-9]*.py"))
    if filters:
        files = [f for f in files if any(f.name.startswith(text) for text in filters)]
    return files


def resolve_allure_dir():
    """Resolve the Allure results directory matching report/common.py."""
    raw = os.getenv("REPORT_ALLURE_RESULTS_DIR")
    if raw is None:
        try:
            from dotenv import dotenv_values
        except ImportError:
            dotenv_values = None
        if dotenv_values is not None:
            for env_file in (FOLDER / ".env.report", PROJECT_ROOT / ".env"):
                if env_file.is_file():
                    val = dotenv_values(env_file).get("REPORT_ALLURE_RESULTS_DIR")
                    if val is not None:
                        raw = val
                        break
    path = Path(raw if raw is not None else "allure-results")
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def run_one(file):
    """Run one test file. Returns (status, seconds)."""
    log_path = LOG_DIR / f"{file.stem}.log"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        try:
            result = subprocess.run(
                [sys.executable, file.name],
                cwd=FOLDER,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_SECONDS,
            )
            if result.returncode == 0:
                status = "PASS"
            elif result.returncode == 2:
                status = "BLOCKED"
            else:
                status = "FAIL"
        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
    return status, time.time() - start


def main():
    """Discover and execute report test scripts sequentially, printing a summary."""
    tests = find_tests(sys.argv[1:])
    if not tests:
        print("No test files found.")
        return 1

    LOG_DIR.mkdir(exist_ok=True)
    print(f"Running {len(tests)} test(s). Logs are in: {LOG_DIR}\n")

    results = []
    for number, file in enumerate(tests, start=1):
        print(f"[{number}/{len(tests)}] {file.stem} ... ", end="", flush=True)
        status, seconds = run_one(file)
        print(f"{status} ({seconds:.0f}s)")
        results.append((file.stem, status))

    passed = sum(1 for _, st in results if st == "PASS")
    blocked = [(name, st) for name, st in results if st == "BLOCKED"]
    failed = [(name, st) for name, st in results if st not in ("PASS", "BLOCKED")]

    print(f"\nPassed: {passed}   Blocked: {len(blocked)}   Failed/Timeout: {len(failed)}")
    for name, status in blocked + failed:
        print(f"  {status:8} {name}   (see logs/{name}.log)")

    allure_dir = resolve_allure_dir()
    try:
        serve_target = os.path.relpath(allure_dir, Path.cwd())
    except ValueError:
        serve_target = str(allure_dir)
    print(f"\nAllure results directory: {allure_dir}")
    print(f"Generate HTML report with: allure serve {serve_target}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
