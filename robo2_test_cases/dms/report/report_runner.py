"""
Execution engine for Report test cases using Selenium POM, Allure, and Excel reporting.
Works directly with dms/report/common.py (LoginPage, BrowserManager, EvidenceManager, ExcelReporter).
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import traceback

# Ensure both the report folder and project root (dms/) are on sys.path
REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent

for _p in (str(REPORT_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.chdir(PROJECT_ROOT)
os.environ["SHEET_NAME"] = "Report"

from report import common as c  # noqa: E402
from report.allure_reporter import AllureReporter  # noqa: E402
from report.pages.report_page import ReportPage  # noqa: E402
from report.pages.requested_downloads_page import RequestedDownloadsPage  # noqa: E402
from report.report_cases import get_case  # noqa: E402
from report.report_config import (  # noqa: E402
    ReportConfigError,
    date_selectors,
    expected_value,
    filter_values,
    get_profile,
    table_selector,
)


class BlockedTest(RuntimeError):
    """Raised when a test cannot be evaluated because required role credentials or test data are missing."""


def _expected_text(visibility: str, role: str) -> str:
    key_by_visibility = {
        "own": "REPORT_EXPECTED_OWN_TEXT",
        "all": "REPORT_EXPECTED_OTHER_TEXT",
        "related": "REPORT_EXPECTED_RELATED_TEXT",
        "department": "REPORT_EXPECTED_DEPARTMENT_TEXT",
    }
    base_key = key_by_visibility.get(visibility)
    if not base_key:
        return ""
    role_key = f"{base_key}_{role.upper()}"
    return expected_value(role_key) or expected_value(base_key)


def _case_setting(base_key: str, case: dict) -> str:
    feature_slug = "_".join(
        "".join(ch.lower() if ch.isalnum() else " " for ch in case["feature"]).split()
    )
    return expected_value(f"{base_key}_{feature_slug.upper()}") or expected_value(base_key)


def _verify_visibility(page: ReportPage, visibility: str, role: str) -> None:
    if visibility == "denied":
        page.assert_denied()
        return

    page.assert_accessible()
    if visibility in {"own", "all", "related", "department"}:
        expected = _expected_text(visibility, role)
        if not expected:
            env_key = {
                "own": "REPORT_EXPECTED_OWN_TEXT",
                "all": "REPORT_EXPECTED_OTHER_TEXT",
                "related": "REPORT_EXPECTED_RELATED_TEXT",
                "department": "REPORT_EXPECTED_DEPARTMENT_TEXT",
            }[visibility] + f"_{role.upper()} (or the shared base setting)"
            raise BlockedTest(f"Permission scope cannot be verified without {env_key}.")

        page.assert_table_contains(expected, f"{visibility}-scope record")

        if visibility == "own":
            other = (
                expected_value(f"REPORT_EXPECTED_OTHER_TEXT_{role.upper()}")
                or expected_value("REPORT_EXPECTED_OTHER_TEXT")
            )
            if not other:
                raise BlockedTest(
                    "Set REPORT_EXPECTED_OTHER_TEXT (or the role-specific REPORT_EXPECTED_OTHER_TEXT_<ROLE>) "
                    "so the restricted report can verify that another user's row is not exposed."
                )
            page.assert_table_not_contains(
                other, "another user's record", allow_with_text=expected
            )


def _run_export_buttons(
    page: ReportPage,
    actions: list[str],
    download_dir: Path,
    allow_queued: bool = False,
) -> list[Path]:
    downloaded: list[Path] = []
    for action in actions:
        before = {path.name for path in download_dir.glob("*") if path.is_file()}
        if action.casefold() == "print":
            page.driver.execute_script(
                "window.__reportPrintCalled=false; "
                "window.print=function(){window.__reportPrintCalled=true;};"
            )
        page.click_action(action)
        if action.casefold() in {"csv", "excel"}:
            extension = ".csv" if action.casefold() == "csv" else ".xlsx"
            try:
                downloaded.append(
                    page.wait_for_download(
                        download_dir,
                        before,
                        extension,
                        timeout=12 if allow_queued else 30,
                    )
                )
            except TimeoutError:
                if not allow_queued:
                    raise
        elif action.casefold() == "print":
            page.wait.until(
                lambda d: bool(d.execute_script("return window.__reportPrintCalled === true"))
            )
        elif action.casefold() == "copy":
            page.assert_accessible()
        elif action.casefold() == "download":
            # A download menu may open or queue a background job in Requested Downloads.
            pass
    return downloaded


def _verify_requested_download(driver, wait) -> None:
    expected = expected_value("REPORT_EXPECTED_DOWNLOAD_TEXT")
    requested_page = RequestedDownloadsPage(driver, wait)
    requested_page.open(c.REQUESTED_DOWNLOAD_URL)
    requested_page.assert_download_request_visible(expected)


def _run_operation(case: dict, page: ReportPage, driver, wait) -> str:
    action = case["action"]
    download_dir = Path(c.DOWNLOAD_DIR)
    download_dir.mkdir(parents=True, exist_ok=True)

    if action in ("open", "scope", "deny", "multi_scope"):
        return "Report access and visibility checks completed."

    if action in ("search", "filter"):
        expected = _case_setting("REPORT_EXPECTED_FILTER_TEXT", case)
        if not expected:
            raise ReportConfigError("Set REPORT_EXPECTED_FILTER_TEXT in report/.env.report before running this test.")
        page.apply_label_filters(filter_values(case["filter_labels"]), expected)
        return f"Applied report filters: {', '.join(case['filter_labels'])}."

    if action == "date":
        date_from = expected_value("REPORT_DATE_FROM")
        date_to = expected_value("REPORT_DATE_TO")
        expected = _case_setting("REPORT_EXPECTED_DATE_TEXT", case)
        if not date_from or not date_to:
            raise ReportConfigError("Set REPORT_DATE_FROM and REPORT_DATE_TO in report/.env.report before running this test.")
        if not expected:
            raise ReportConfigError("Set REPORT_EXPECTED_DATE_TEXT in report/.env.report before running this test.")
        from_sel, to_sel = date_selectors()
        page.apply_date_range(date_from, date_to, expected, from_selector=from_sel, to_selector=to_sel)
        return "Applied the configured date range and verified a known row in the result."

    if action == "sort":
        page.sort_columns(case["sort_labels"])
        return f"Verified sorting on: {', '.join(case['sort_labels'])}."

    if action == "export":
        if case.get("page_size"):
            for size in case["page_size"].split(","):
                page.choose_page_size(size.strip())
        downloaded = _run_export_buttons(
            page,
            case["export_actions"],
            download_dir,
            allow_queued=(case.get("download_mode") == "requested"),
        )
        if case.get("download_mode") == "requested":
            _verify_requested_download(driver, wait)
        return f"Export controls completed: {', '.join(case['export_actions'])}. " + (
            f"Downloaded: {', '.join(path.name for path in downloaded)}." if downloaded else ""
        )

    if action == "download_direct":
        actions = case.get("export_actions") or [os.getenv("REPORT_DIRECT_EXPORT_ACTION", "CSV")]
        downloaded = _run_export_buttons(page, actions, download_dir, allow_queued=False)
        expected_files = [a for a in actions if a.casefold() in {"csv", "excel"}]
        if len(downloaded) < len(expected_files):
            raise AssertionError("One or more direct report export files were not created.")
        if not downloaded:
            raise AssertionError("The report export control was clicked, but no download file was created.")
        return "Direct report downloads verified: " + ", ".join(path.name for path in downloaded) + "."

    if action == "download_requested":
        actions = case.get("export_actions") or ["Download"]
        _run_export_buttons(page, actions[:1], download_dir, allow_queued=True)
        _verify_requested_download(driver, wait)
        return "Report request is visible in Requested Downloads."

    raise BlockedTest(f"No execution implementation is mapped for action '{action}'.")


def _execute_case(case: dict, reporter: AllureReporter, driver, wait) -> str:
    login_page = c.LoginPage(driver, wait, reporter=reporter)
    report_page = ReportPage(driver, wait, table_selector=table_selector())
    messages: list[str] = []

    for index, (role, visibility) in enumerate(case["profiles"]):
        profile = get_profile(role)
        if index > 0:
            login_page.switch_user(profile.username, profile.password)
        else:
            login_page.login_as(profile.username, profile.password)

        with reporter.step(f"Open {case['feature']} page ({case['route']})"):
            report_page.open(c.BASE_URL, case["route"])

        with reporter.step(f"Verify report access ({visibility}) for role '{role}'"):
            _verify_visibility(report_page, visibility, role)

        if case["action"] == "multi_scope":
            messages.append(f"{role}: {visibility} report access verified")
            continue

        if case["action"] not in ("scope", "deny", "open"):
            with reporter.step(f"Execute {case['action']} operation"):
                messages.append(_run_operation(case, report_page, driver, wait))
        else:
            messages.append(f"{role}: {visibility} report visibility verified")

    return " ".join(messages)


def run_report_case(test_case_id: str) -> None:
    case = get_case(test_case_id)
    reporter = c.create_allure_reporter()
    report_url = f"{c.BASE_URL}{case['route']}"

    reporter.start_test(
        test_case_id,
        case["functional_area"],
        case["functional_area"],
        f"Steps from Report worksheet:\n{case['steps']}\n\nExpected result:\n{case['expected_result']}",
        report_url,
    )

    driver = None
    wait = None
    status = "failed"
    excel_status = "Fail"
    actual = ""
    shot_paths: list[str] = []
    error: BaseException | None = None

    try:
        # 1. Verify Excel row & file lock (logs Allure step automatically via common.py)
        c.check_excel_ready(test_case_id)

        # 2. Verify required role credentials before launching Chrome
        with reporter.step("Validate configured test account profiles"):
            for profile_key, _visibility in case["profiles"]:
                get_profile(profile_key)

        # 3. Launch Chrome WebDriver (logs Allure step automatically via common.py)
        driver, wait = c.start_browser()

        # 4. Run test steps using POM classes
        actual = _execute_case(case, reporter, driver, wait)
        status = "passed"
        excel_status = "Pass"

        # 5. Save screenshot to disk for Excel AND attach to Allure automatically
        with reporter.step("Capture passing evidence"):
            shot_paths.append(c.save_shot(driver, test_case_id, "report", "PASS"))

    except (ReportConfigError, BlockedTest) as exc:
        error = exc
        status = "skipped"
        excel_status = "Blocked"
        actual = f"Blocked - {exc}"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "report", "BLOCKED"))
            except Exception:
                pass
        reporter.attach_text(actual, "Execution prerequisite")

    except (SystemExit, c.SetupError) as exc:
        error = exc
        actual = f"Setup failed - {c.short(exc)}"
        status = "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "setup", "FAIL"))
            except Exception:
                pass
        c.attach_failure_diagnostics(driver, traceback.format_exc())

    except Exception as exc:
        error = exc
        actual = c.short(exc)
        status = "failed" if isinstance(exc, AssertionError) else "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "report", "FAIL"))
            except Exception:
                pass
        c.attach_failure_diagnostics(driver, traceback.format_exc())

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            # Writes status, actual result, date, tester, and hyperlinked screenshot to Excel
            c.write_result(test_case_id, actual, excel_status, shot_paths=shot_paths)
        except Exception as excel_error:
            reporter.attach_text(
                f"Excel update failed: {excel_error}\n{traceback.format_exc()}",
                "Excel reporting error",
            )
            if status == "passed":
                status = "broken"
                actual += f" | Excel reporting failed: {excel_error}"

        reporter.finish(status, actual, error)
        c.set_active_reporter(None)

    print(f"\n{test_case_id}: {excel_status} - {actual}")
    if status in ("failed", "broken"):
        raise SystemExit(1)
    if status == "skipped":
        raise SystemExit(2)