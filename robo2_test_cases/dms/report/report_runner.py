"""Execution engine for Report scripts; intentionally mirrors common.run() without changing DMS."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import traceback

# Resolve the project root before importing common.py. This keeps relative paths in
# the existing root .env and Excel configuration working from the GUI worker.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
os.environ["SHEET_NAME"] = "Report"

import common as c  # noqa: E402 - env and working directory must be set first

# common.py loads the root .env; report_config.py then adds report/.env.report. Normalize a relative workbook path against the
# project root because the GUI worker launches nested scripts from their folder.
_excel_path = os.environ.get("EXCEL_PATH") or c.EXCEL_PATH
if _excel_path:
    _path = Path(_excel_path)
    os.environ["EXCEL_PATH"] = str((_path if _path.is_absolute() else PROJECT_ROOT / _path).resolve())

from allure_commons.types import AttachmentType  # noqa: E402

from report.allure_reporter import AllureReporter  # noqa: E402
from report.pages.report_page import ReportPage  # noqa: E402
from report.pages.requested_downloads_page import RequestedDownloadsPage  # noqa: E402
from report.report_cases import get_case  # noqa: E402
from report.report_config import ReportConfigError, expected_value, filter_values, get_profile  # noqa: E402


class BlockedTest(RuntimeError):
    """A test cannot be evaluated because required role or test data is not configured."""


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
    feature_slug = "_".join("".join(ch.lower() if ch.isalnum() else " " for ch in case["feature"]).split())
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
            other = expected_value(f"REPORT_EXPECTED_OTHER_TEXT_{role.upper()}") or expected_value("REPORT_EXPECTED_OTHER_TEXT")
            if not other:
                raise BlockedTest(
                    "Set REPORT_EXPECTED_OTHER_TEXT (or the role-specific REPORT_EXPECTED_OTHER_TEXT_<ROLE>) "
                    "so the restricted report can verify that another user's row is not exposed."
                )
            page.assert_table_not_contains(other, "another user's record")


def _run_operation(case: dict, page: ReportPage, driver, wait) -> str:
    action = case["action"]
    download_dir = Path(c.DOWNLOAD_DIR)
    download_dir.mkdir(parents=True, exist_ok=True)

    if action in ("open", "scope", "deny", "multi_scope"):
        return "Report access and visibility checks completed."

    if action in ("search", "filter"):
        page.apply_label_filters(
            case["filter_labels"], filter_values(), _case_setting("REPORT_EXPECTED_FILTER_TEXT", case)
        )
        return f"Applied report filters: {', '.join(case['filter_labels'])}."

    if action == "date":
        page.apply_date_range(
            expected_value("REPORT_DATE_FROM"),
            expected_value("REPORT_DATE_TO"),
            _case_setting("REPORT_EXPECTED_DATE_TEXT", case),
        )
        return "Applied the configured date range and verified a known row in the result."

    if action == "sort":
        page.sort_columns(case["sort_labels"])
        return f"Verified sorting on: {', '.join(case['sort_labels'])}."

    if action == "export":
        if case.get("page_size"):
            for size in case["page_size"].split(","):
                page.choose_page_size(size.strip())
        downloaded = _run_export_buttons(page, case["export_actions"], download_dir, case.get("download_mode"))
        if case.get("download_mode") == "requested":
            _verify_requested_download(page, driver, wait, case)
        return f"Export controls completed: {', '.join(case['export_actions'])}. " + (
            f"Downloaded: {', '.join(path.name for path in downloaded)}." if downloaded else ""
        )

    if action == "download_direct":
        actions = case.get("export_actions") or [os.getenv("REPORT_DIRECT_EXPORT_ACTION", "CSV")]
        downloaded = _run_export_buttons(page, actions, download_dir, allow_queued=False)
        if len(downloaded) < len([action for action in actions if action.casefold() in {"csv", "excel"}]):
            raise AssertionError("One or more direct report export files were not created.")
        if not downloaded:
            raise AssertionError("The report export control was clicked, but no download file was created.")
        return "Direct report downloads verified: " + ", ".join(path.name for path in downloaded) + "."

    if action == "download_requested":
        actions = case.get("export_actions") or ["Download"]
        _run_export_buttons(page, actions[:1], download_dir, allow_queued=True)
        _verify_requested_download(page, driver, wait, case)
        return "Report request is visible in Requested Downloads."

    raise BlockedTest(f"No execution implementation is mapped for action '{action}'.")


def _run_export_buttons(page: ReportPage, actions: list[str], download_dir: Path, allow_queued: bool = False) -> list[Path]:
    downloaded: list[Path] = []
    for action in actions:
        before = {path.name for path in download_dir.glob("*") if path.is_file()}
        if action.casefold() == "print":
            page.driver.execute_script("window.__reportPrintCalled=false; window.print=function(){window.__reportPrintCalled=true;};")
        page.click_action(action)
        if action.casefold() in {"csv", "excel"}:
            extension = ".csv" if action.casefold() == "csv" else ".xlsx"
            try:
                downloaded.append(page.wait_for_download(download_dir, before, extension, timeout=12 if allow_queued else 30))
            except TimeoutError:
                if not allow_queued:
                    raise
        elif action.casefold() == "print":
            page.wait.until(lambda d: bool(d.execute_script("return window.__reportPrintCalled === true")))
        elif action.casefold() == "copy":
            page.assert_accessible()
        elif action.casefold() == "download":
            # A download menu may open; a child option is selected by the caller or
            # the application may create the requested-download job immediately.
            pass
    return downloaded


def _verify_requested_download(page: ReportPage, driver, wait, case: dict) -> None:
    from report.pages.requested_downloads_page import RequestedDownloadsPage
    import common as common_module

    expected = expected_value("REPORT_EXPECTED_DOWNLOAD_TEXT")
    requested_page = RequestedDownloadsPage(driver, wait)
    requested_page.open(common_module.REQUESTED_DOWNLOAD_URL)
    requested_page.assert_download_request_visible(expected)


def _execute_case(case: dict, reporter: AllureReporter, driver, wait) -> str:
    roles = case["profiles"]
    messages = []
    for index, (role, visibility) in enumerate(roles):
        profile = get_profile(role)
        if index:
            with reporter.step(f"Switch session to role: {role}"):
                c.logout(driver)
                c.login_as(driver, wait, profile.username, profile.password)
        else:
            with reporter.step(f"Login as role: {role}"):
                c.login_as(driver, wait, profile.username, profile.password)

        page = ReportPage(driver, wait)
        with reporter.step(f"Open {case['feature']} page"):
            page.open(c.BASE_URL, case["route"])

        with reporter.step(f"Verify report access: {visibility}"):
            _verify_visibility(page, visibility, role)

        if case["action"] == "multi_scope":
            messages.append(f"{role}: report access verified")
            continue

        # Run the functional operation only after the permission check succeeds.
        if case["action"] not in ("scope", "deny", "open"):
            with reporter.step(f"Execute {case['action']} operation"):
                messages.append(_run_operation(case, page, driver, wait))
        else:
            messages.append(f"{role}: {visibility} report visibility verified")

    return " ".join(messages)


def run_report_case(test_case_id: str) -> None:
    case = get_case(test_case_id)
    results_dir = Path(os.getenv("REPORT_ALLURE_RESULTS_DIR", "allure-results"))
    if not results_dir.is_absolute():
        results_dir = PROJECT_ROOT / results_dir
    reporter = AllureReporter(results_dir)
    report_url = (c.BASE_URL or "").rstrip("/") + case["route"]
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
        with reporter.step("Validate Excel test case row"):
            c.check_excel_ready(test_case_id)
        with reporter.step("Validate configured test account profiles"):
            for profile_key, _visibility in case["profiles"]:
                get_profile(profile_key)
        with reporter.step("Start Chrome WebDriver"):
            driver, wait = c.start_browser()
        actual = _execute_case(case, reporter, driver, wait)
        status = "passed"
        excel_status = "Pass"
        with reporter.step("Capture passing evidence"):
            shot_paths.append(c.save_shot(driver, test_case_id, "report", "PASS"))
        reporter.attach_file(Path(shot_paths[-1]), "Passing screenshot", AttachmentType.PNG)

    except (ReportConfigError, BlockedTest) as exc:
        error = exc
        status = "skipped"
        excel_status = "Blocked"
        actual = f"Blocked - {exc}"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "report", "BLOCKED"))
                reporter.attach_file(Path(shot_paths[-1]), "Blocked screenshot", AttachmentType.PNG)
            except Exception:
                pass
        reporter.attach_text(actual, "Execution prerequisite")

    except SystemExit as exc:
        error = exc
        actual = f"Setup failed - {c.short(exc)}"
        status = "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "setup", "FAIL"))
                reporter.attach_file(Path(shot_paths[-1]), "Setup failure screenshot", AttachmentType.PNG)
            except Exception:
                pass

    except Exception as exc:
        error = exc
        actual = c.short(exc)
        status = "failed" if isinstance(exc, AssertionError) else "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(c.save_shot(driver, test_case_id, "report", "FAIL"))
                reporter.attach_file(Path(shot_paths[-1]), "Failure screenshot", AttachmentType.PNG)
                debug_path = Path(c.DEBUG_DIR) / f"{test_case_id}_report.html"
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                debug_path.write_text(driver.page_source, encoding="utf-8")
                reporter.attach_file(debug_path, "Failure page HTML", AttachmentType.HTML)
            except Exception:
                pass
        reporter.attach_text(traceback.format_exc(), "Python traceback")

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            with reporter.step("Write result to Report worksheet"):
                c.write_result(test_case_id, actual, excel_status, shot_paths=shot_paths)
        except Exception as excel_error:
            reporter.attach_text(f"Excel update failed: {excel_error}\n{traceback.format_exc()}", "Excel reporting error")
            if status == "passed":
                status = "broken"
                actual += f" | Excel reporting failed: {excel_error}"
        reporter.finish(status, actual, error)

    print(f"\n{test_case_id}: {excel_status} - {actual}")
    if status in ("failed", "broken"):
        raise SystemExit(1)
    if status == "skipped":
        # Keep the GUI/CLI return code non-zero so a blocked test is not shown as Pass.
        raise SystemExit(2)

