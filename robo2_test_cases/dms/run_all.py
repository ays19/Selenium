"""
Run the DMS test scripts one after another, with one terminal command.

    python run_all.py                 run every tcXXX_*.py file
    python run_all.py tc014 tc022     run only the files whose name starts with these

Each test runs in its own process (its own Chrome window), so one broken test
cannot stop the others. Output of failed, blocked, or timed-out tests is saved
in logs/<test file>.log and Allure 2 results are written to allure-results/.
Keep the Excel file closed while this runs.
"""
import os
from pathlib import Path
import subprocess
import sys
import time

FOLDER = Path(__file__).resolve().parent
LOG_DIR = FOLDER / "logs"
TIMEOUT_SECONDS = 600  # give up on one test after 10 minutes


def find_tests(filters):
    files = sorted(FOLDER.glob("tc*.py"))
    if filters:
        files = [f for f in files if any(f.name.startswith(text) for text in filters)]
    return files


def run_one(file):
    """Run one test file. Save log only if non-passing. Returns (status, seconds)."""
    log_path = LOG_DIR / f"{file.stem}.log"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    start = time.time()
    output = ""
    try:
        result = subprocess.run(
            [sys.executable, file.name],
            cwd=FOLDER,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SECONDS,
        )
        output = result.stdout or ""
        if result.returncode == 0:
            status = "PASS"
        elif result.returncode == 2:
            status = "BLOCKED"
        else:
            status = "FAIL"
    except subprocess.TimeoutExpired as exc:
        status = "TIMEOUT"
        if isinstance(exc.output, bytes):
            output = exc.output.decode("utf-8", errors="replace")
        else:
            output = exc.output or ""

    if status == "PASS":
        log_path.unlink(missing_ok=True)
    else:
        LOG_DIR.mkdir(exist_ok=True)
        log_path.write_text(output, encoding="utf-8")

    return status, time.time() - start


def main():
    tests = find_tests(sys.argv[1:])
    if not tests:
        print("No test files found.")
        return 1

    print(f"Running {len(tests)} test(s). Failure logs will be saved in: {LOG_DIR}\n")

    results = []
    for number, file in enumerate(tests, start=1):
        print(f"[{number}/{len(tests)}] {file.stem} ... ", end="", flush=True)
        status, seconds = run_one(file)
        print(f"{status} ({seconds:.0f}s)")
        results.append((file.stem, status))

    if LOG_DIR.is_dir() and not any(LOG_DIR.iterdir()):
        try:
            LOG_DIR.rmdir()
        except OSError:
            pass

    passed = sum(1 for _, st in results if st == "PASS")
    blocked = [(name, st) for name, st in results if st == "BLOCKED"]
    failed = [(name, st) for name, st in results if st not in ("PASS", "BLOCKED")]

    print(f"\nPassed: {passed}   Blocked: {len(blocked)}   Failed/Timeout: {len(failed)}")
    for name, status in blocked + failed:
        print(f"  {status:8} {name}   (see logs/{name}.log)")

    allure_dir = FOLDER / (
        os.getenv("DMS_ALLURE_RESULTS_DIR")
        or os.getenv("ALLURE_RESULTS_DIR")
        or "allure-results"
    )
    print(f"\nAllure results directory: {allure_dir}")
    print("Generate HTML report with: allure serve allure-results")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
