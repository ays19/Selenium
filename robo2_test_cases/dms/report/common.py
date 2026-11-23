"""
Core POM + Data-Driven + Allure + Excel test harness for the Report test suite.

Architecture:
- pages/           -> Selenium Page Object Model classes (LoginPage, ReportPage, RequestedDownloadsPage)
- report_config.py -> Loads credentials & runtime settings from .env.report
- report_data.py   -> Data-driven search/filter inputs, expected texts, and rolling date range
- allure_reporter.py -> Allure 2 step logging and attachments
- common.py        -> ReportSession facade, browser factory, screenshots, Excel reporting, and test runner
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import sys
import traceback
from typing import Callable, Sequence

# Ensure both `dms/report/` and `dms/` are importable regardless of working directory
REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
for _p in (str(REPORT_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from allure_commons.types import AttachmentType  # noqa: E402
from allure_commons.utils import uuid4  # noqa: E402
import openpyxl  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.remote.webdriver import WebDriver  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from report.allure_reporter import AllureReporter  # noqa: E402
from report.pages.login_page import LoginError, LoginPage  # noqa: E402
from report.pages.report_page import ReportPage  # noqa: E402
from report.pages.requested_downloads_page import RequestedDownloadsPage  # noqa: E402
from report.report_config import (  # noqa: E402
    ReportConfigError,
    date_selectors,
    get_profile,
    is_headless,
    table_selector,
)
from report.report_data import (  # noqa: E402
    DEFAULT_DATE_RANGE_DAYS,
    DEFAULT_DOC_TYPE,
    EXPECTED_DOWNLOAD_TEXT,
    expected_scope_texts,
    get_date_range,
    get_filter_data,
)

# =============================================================================
# 1. Runtime Paths & Settings (loaded once via report_config)
# =============================================================================

BASE_URL: str = (os.getenv("BASE_URL") or "").rstrip("/")
TESTER_NAME: str = os.getenv("TESTER_NAME") or ""
SHEET_NAME: str = os.getenv("SHEET_NAME", "Report")
EXCEL_PATH: str = os.getenv("EXCEL_PATH") or ""
EVIDENCE_LINK: str = os.getenv("EVIDENCE_LINK") or ""
EVIDENCE_HEADER: str = os.getenv("EVIDENCE_HEADER", "remark").lower()
HEADER_ROW: int = 4


def _resolve_dir(env_key: str, default_name: str) -> Path:
    path = Path(os.getenv(env_key, default_name))
    resolved = path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


SCREENSHOT_DIR: str = str(_resolve_dir("SCREENSHOT_DIR", "screenshots"))
DOWNLOAD_DIR: str = str(_resolve_dir("DOWNLOAD_DIR", "downloads"))
ALLURE_RESULTS_DIR: Path = _resolve_dir("REPORT_ALLURE_RESULTS_DIR", "allure-results")
REQUESTED_DOWNLOAD_URL: str = f"{BASE_URL}/requested_downloads/view/"

_LAST_SAVED_SHOTS: dict[str, list[str]] = {}


class SetupError(RuntimeError):
    """Raised when browser startup, Excel setup, or login fails."""


class BlockedTest(RuntimeError):
    """Raised when required test data or credentials are missing."""


# =============================================================================
# 2. High-Level POM + Allure Test Session (used by repXXX_*.py scripts)
# =============================================================================

class ReportSession:
    """High-level facade combining Page Objects, test data, and Allure steps."""

    def __init__(self, driver: WebDriver, wait: WebDriverWait, reporter: AllureReporter):
        self.driver = driver
        self.wait = wait
        self.reporter = reporter
        self.login_page = LoginPage(driver, wait, BASE_URL, reporter)
        self.report_page = ReportPage(driver, wait, table_selector=table_selector())
        self.downloads_page = RequestedDownloadsPage(driver, wait)
        self._logged_in = False
        self.current_role = ""
        self.current_username = ""

    def step(self, title: str):
        return self.reporter.step(title)

    def login_as_role(self, role_key: str) -> str:
        profile = get_profile(role_key)
        if self._logged_in:
            self.login_page.switch_user(profile.username, profile.password)
        else:
            self.login_page.login_as(profile.username, profile.password)
            self._logged_in = True
        self.current_role = role_key
        self.current_username = profile.username
        return profile.username

    def open_report(self, route: str, check_accessible: bool = True) -> None:
        with self.step(f"Open report page ({route})"):
            self.report_page.open(BASE_URL, route)
            if check_accessible:
                self.report_page.assert_accessible()

    def open_custom_report(
        self,
        route: str,
        report_name: str = "",
        check_accessible: bool = True,
    ) -> str:
        self.open_report(route, check_accessible=False)
        with self.step(f"Open custom report card ({report_name or 'first available'})"):
            opened_name = self.report_page.open_custom_report(report_name)
            if check_accessible:
                self.report_page.assert_accessible()
        return opened_name

    def select_document_type(self, doc_type: str = "") -> str:
        target = (doc_type or DEFAULT_DOC_TYPE).strip()
        if not target:
            raise BlockedTest("DEFAULT_DOC_TYPE is not set in report_data.py.")
        with self.step(f"Select Document Type: '{target}'"):
            self.report_page.select_document_type(target)
        return target

    def verify_has_rows(self, context: str = "") -> str:
        label = context or f"role '{self.current_role}'"
        with self.step(f"Verify report rows are loaded for {label}"):
            count = self.report_page.assert_has_rows(label)
        return f"Role '{self.current_role}': report loaded with {count} row(s)."

    def verify_document_type_rows(self, doc_type: str = "", verify_text: bool = False) -> str:
        target = self.select_document_type(doc_type)
        with self.step(f"Verify filtered rows for Document Type '{target}'"):
            count = self.report_page.assert_has_rows(f"doc-type '{target}'")
            if verify_text:
                self.report_page.assert_table_contains(target, "Document Type filtered result")
        return (
            f"Role '{self.current_role}': verified Document Type '{target}' "
            f"({count} row(s) visible)."
        )

    def verify_columns(self, expected_columns: list[str]) -> str:
        with self.step(f"Verify report columns: {', '.join(expected_columns)}"):
            self.report_page.assert_headers_present(expected_columns)
        return f"Verified columns: {', '.join(expected_columns)}."

    def verify_scope(self, visibility: str, role_key: str = "") -> str:
        role = (role_key or self.current_role).strip().lower()
        with self.step(f"Verify report visibility scope: '{visibility}'"):
            if visibility == "denied":
                self.report_page.assert_denied()
                return f"Role '{role}': access denied as expected."

            self.report_page.assert_accessible()
            if visibility == "accessible":
                return f"Role '{role}': report is accessible and loaded."

            own_text, other_text = expected_scope_texts(role)

            if visibility == "own":
                own_text = (self.current_username or own_text).strip()
                if not own_text or not other_text:
                    raise BlockedTest(
                        "Set REPORT_USERNAME and REPORT_MANAGER_USERNAME in .env.report."
                    )
                self.report_page.assert_table_contains(own_text, "own-scope record")
                self.report_page.assert_table_not_contains(
                    other_text, "another user's record", allow_with_text=own_text
                )
                return f"Role '{role}': sees own record ('{own_text}') and cannot see '{other_text}'."

            if visibility == "all":
                if not other_text:
                    raise BlockedTest(
                        f"Configure ROLE_EXPECTED_ALL_TEXT for '{role}' in report_data.py."
                    )
                self.report_page.assert_table_contains(other_text, "all-users record")
                return f"Role '{role}': verified all-users record ('{other_text}')."

            return f"Role '{role}': report access verified."

    def verify_other_user_visible(self, own_username: str = "") -> str:
        """Verify at least one visible row belongs to a user other than the logged-in user."""
        current_user = (own_username or get_profile(self.current_role).username).strip()
        with self.step(f"Verify records from another user (besides '{current_user}') are visible"):
            other_user = self.report_page.assert_has_other_user_record(current_user)
        return (
            f"Role '{self.current_role}': verified another user's record "
            f"('{other_user}') is visible for '{current_user}'."
        )

    def verify_user_dropdown_scope(self, visibility: str) -> str:
        """Verify scope on reports where the user filter is a dropdown instead of a table column."""
        with self.step(f"Verify user dropdown visibility scope: '{visibility}'"):
            count = self.report_page.assert_has_rows(f"role '{self.current_role}'")
            dropdown_text = self.report_page.user_dropdown_options_text()
            page_text = self.report_page.body_text().casefold()
            own_text, other_text = expected_scope_texts(self.current_role)

            if visibility == "own":
                own_text = (self.current_username or own_text).strip()
                if own_text.casefold() not in dropdown_text and own_text.casefold() not in page_text:
                    raise AssertionError(f"Expected own user '{own_text}' on the report.")
                if other_text.casefold() in dropdown_text or other_text.casefold() in page_text:
                    raise AssertionError(
                        f"Unexpected other user '{other_text}' was accessible to '{self.current_role}'."
                    )
                return (
                    f"Role '{self.current_role}': sees own records for '{own_text}' "
                    f"({count} row(s)) and cannot access '{other_text}'."
                )

            if other_text.casefold() not in dropdown_text:
                raise AssertionError(
                    f"Expected user '{other_text}' in user dropdown for '{self.current_role}'."
                )
            return (
                f"Role '{self.current_role}': accessed report ({count} row(s)) "
                f"with all-users selector including '{other_text}'."
            )

    def filter_by_user(self, username: str = "") -> str:
        """Select a user from the report's user dropdown and verify filtered rows load."""
        _own, other = expected_scope_texts(self.current_role)
        target = (username or other or _own).strip()
        if not target:
            raise BlockedTest("No target username available for user filter.")

        with self.step(f"Filter report by user '{target}'"):
            selected = self.report_page.select_user_from_dropdown(target)
            count = self.report_page.assert_has_rows(f"user '{selected}'")
        return f"Filtered by user '{selected}' ({count} row(s) visible)."

    def search_or_filter(
        self,
        labels: list[str],
        report_key: str = "",
        expected_text: str = "",
    ) -> str:
        """Apply data-driven search/filter values from report_data.py (with live discovery for dynamic IDs)."""
        filters_dict, data_expected = get_filter_data(report_key, labels)

        missing_labels = [lbl for lbl in labels if lbl not in filters_dict]
        if missing_labels:
            discovered = self.report_page.discover_filter_values(missing_labels)
            for lbl in missing_labels:
                if discovered.get(lbl):
                    filters_dict[lbl] = discovered[lbl]

        still_missing = [lbl for lbl in labels if lbl not in filters_dict]
        if still_missing:
            raise BlockedTest(
                f"Missing filter values for {still_missing}. Add them to REPORT_FILTERS['{report_key}'] in report_data.py."
            )

        ordered_filters = {lbl: filters_dict[lbl] for lbl in labels}
        expected_row = (expected_text or data_expected).strip()

        with self.step(f"Search/Filter report by: {', '.join(labels)}"):
            self.report_page.apply_label_filters(ordered_filters, expected_row)
        return f"Searched/Filtered by {', '.join(labels)} and verified matching rows."

    def filter_by_date(
        self,
        days_back: int = DEFAULT_DATE_RANGE_DAYS,
        expected_text: str = "",
    ) -> str:
        """Apply a rolling date range and verify visible table dates fall within the range."""
        date_from, date_to = get_date_range(days_back)
        from_sel, to_sel = date_selectors()

        with self.step(f"Filter by date range ({date_from} to {date_to})"):
            self.report_page.apply_date_range(
                date_from,
                date_to,
                expected_text=expected_text,
                from_selector=from_sel,
                to_selector=to_sel,
            )
        return f"Applied date range ({date_from} to {date_to}) and verified results."

    def sort_by(self, columns: list[str]) -> str:
        with self.step(f"Sort report columns: {', '.join(columns)}"):
            self.report_page.sort_columns(columns)
        return f"Verified sorting on columns: {', '.join(columns)}."

    def export(
        self,
        actions: list[str],
        page_sizes: Sequence[str] = (),
        requested_download: bool = False,
    ) -> str:
        download_dir = Path(DOWNLOAD_DIR)
        if page_sizes:
            with self.step(f"Verify page sizes: {', '.join(page_sizes)}"):
                for size in page_sizes:
                    self.report_page.choose_page_size(size.strip())

        downloaded: list[Path] = []
        queued_download = False

        with self.step(f"Execute export actions: {', '.join(actions)}"):
            for action in actions:
                before = {p.name for p in download_dir.glob("*") if p.is_file()}
                if action.casefold() == "print":
                    self.driver.execute_script(
                        "window.__reportPrintCalled=false; "
                        "window.print=function(){window.__reportPrintCalled=true;};"
                    )

                self.report_page.click_action(action)

                if action.casefold() in {"csv", "excel"}:
                    ext = ".csv" if action.casefold() == "csv" else ".xlsx"
                    try:
                        file_path = self.report_page.wait_for_download(
                            download_dir,
                            before,
                            ext,
                            timeout=12 if requested_download else 30,
                            allow_queued=True,
                        )
                        if file_path is None:
                            queued_download = True
                        else:
                            downloaded.append(file_path)
                    except TimeoutError:
                        if not requested_download:
                            raise
                elif action.casefold() == "print":
                    self.wait.until(
                        lambda d: bool(d.execute_script("return window.__reportPrintCalled === true"))
                    )
                elif action.casefold() == "copy":
                    self.report_page.assert_accessible()

        verify_requested = requested_download or queued_download
        if verify_requested:
            with self.step("Verify entry in Requested Downloads page"):
                self.downloads_page.open(REQUESTED_DOWNLOAD_URL)
                self.downloads_page.assert_download_request_visible(EXPECTED_DOWNLOAD_TEXT)

        files_info = f" Downloaded: {', '.join(p.name for p in downloaded)}." if downloaded else ""
        req_info = " Verified in Requested Downloads." if verify_requested else ""
        return f"Completed export actions ({', '.join(actions)}).{files_info}{req_info}"


# =============================================================================
# 3. Browser, Screenshot & Allure Utilities
# =============================================================================

def create_allure_reporter() -> AllureReporter:
    return AllureReporter(ALLURE_RESULTS_DIR)


def start_browser(timeout: int = 15) -> tuple[WebDriver, WebDriverWait]:
    options = Options()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "profile.default_content_setting_values.automatic_downloads": 1,
        },
    )
    if is_headless():
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    if not is_headless():
        driver.maximize_window()

    wait = WebDriverWait(
        driver,
        timeout,
        ignored_exceptions=(NoSuchElementException, StaleElementReferenceException),
    )
    return driver, wait


def save_shot(
    driver: WebDriver,
    test_case_id: str,
    slug: str,
    result: str,
    reporter: AllureReporter | None = None,
) -> str:
    tc_id = str(test_case_id).strip()
    tc_folder = Path(SCREENSHOT_DIR).resolve() / tc_id
    tc_folder.mkdir(parents=True, exist_ok=True)

    file_path = (tc_folder / f"{tc_id}_{slug}_{result}.png").resolve()
    driver.save_screenshot(str(file_path))
    _LAST_SAVED_SHOTS.setdefault(tc_id, []).append(str(file_path))
    print(f"   [Screenshot saved]: {file_path}")

    if reporter and reporter.test_uuid:
        reporter.attach_file(
            file_path,
            name=f"{tc_id} ({result}) Screenshot",
            attachment_type=AttachmentType.PNG,
        )
    return str(file_path)


def attach_failure_diagnostics(
    driver: WebDriver | None,
    tb_text: str = "",
    reporter: AllureReporter | None = None,
) -> None:
    if not (reporter and reporter.test_uuid):
        return
    if driver:
        try:
            reporter.lifecycle.attach_data(
                uuid4(),
                driver.page_source,
                name="Failure Page DOM (HTML)",
                attachment_type=AttachmentType.HTML,
                parent_uuid=reporter.test_uuid,
            )
        except Exception:
            pass
    if tb_text:
        reporter.attach_text(tb_text, "Python Traceback")


def short(error: BaseException) -> str:
    lines = str(error).splitlines()
    first = lines[0].strip()[:140] if lines else ""
    if not first:
        try:
            frames = [
                f for f in traceback.extract_tb(error.__traceback__)
                if "site-packages" not in f.filename
                and f.name not in ("run_report_test", "<module>", "<lambda>")
            ]
            if frames:
                chain = " > ".join(f.name for f in frames)
                first = f"happened in {chain} (line {frames[-1].lineno})"
        except Exception:
            pass
    return f"{type(error).__name__}: {first}"


# =============================================================================
# 4. Excel Validation & Result Reporting
# =============================================================================

def _active_excel_and_sheet() -> tuple[str, str]:
    raw_excel = os.environ.get("EXCEL_PATH") or EXCEL_PATH
    if not raw_excel:
        raise SystemExit("EXCEL_PATH is not set in .env or environment.")
    excel_path = Path(raw_excel)
    if not excel_path.is_absolute():
        excel_path = (PROJECT_ROOT / excel_path).resolve()
    sheet_name = os.environ.get("SHEET_NAME") or SHEET_NAME or "Report"
    return str(excel_path), sheet_name


def _find_row_and_columns(ws, test_case_id: str) -> tuple[int | None, dict[str, int | None]]:
    headers: dict[int, str] = {}
    for h_row in (HEADER_ROW, 1, 2, 3, 5):
        for col in range(1, ws.max_column + 1):
            text = str(ws.cell(h_row, col).value or "").strip().lower()
            if text:
                headers[col] = text
        if any("status" in t or "actual" in t for t in headers.values()):
            break
        headers.clear()

    def _col_of(*keywords: str) -> int | None:
        for kw in keywords:
            for col, text in headers.items():
                if kw in text:
                    return col
        return None

    columns = {
        "actual": _col_of("actual"),
        "status": _col_of("status"),
        "evidence": _col_of(EVIDENCE_HEADER, "remark", "evidence", "screenshot", "screen shot"),
        "date": _col_of("date"),
        "tester": _col_of("tester"),
    }

    target_id = str(test_case_id).strip().lower()
    target_row = next(
        (
            r for r in range(1, ws.max_row + 1)
            if str(ws.cell(r, 1).value or "").strip().lower() == target_id
        ),
        None,
    )
    return target_row, columns


def _resolve_latest_screenshot(
    test_case_id: str, shot_paths: Sequence[str] | None = None
) -> str | None:
    tc_id = str(test_case_id).strip()
    candidates = list(shot_paths or []) or list(_LAST_SAVED_SHOTS.get(tc_id, []))
    valid = [str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()]

    if not valid:
        tc_folder = Path(SCREENSHOT_DIR).resolve() / tc_id
        if tc_folder.is_dir():
            pngs = sorted(tc_folder.glob("*.png"), key=lambda item: item.stat().st_mtime)
            valid = [str(p.resolve()) for p in pngs]

    if not valid:
        return None
    fail_shots = [p for p in valid if "_FAIL.png" in p]
    return fail_shots[-1] if fail_shots else valid[-1]


def check_excel_ready(test_case_id: str) -> None:
    excel_path, sheet_name = _active_excel_and_sheet()
    print(f"Checking Excel: {excel_path} [Sheet: {sheet_name}] for {test_case_id}")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
    row, columns = _find_row_and_columns(ws, test_case_id)
    if row is None:
        raise SystemExit(
            f"{test_case_id} not found in column A of sheet '{ws.title}' in {excel_path}"
        )
    missing = [k for k, v in columns.items() if v is None]
    print(f"Row {row} found in '{ws.title}'. Missing columns: {missing or 'none'}")
    try:
        with open(excel_path, "ab"):
            pass
    except PermissionError as exc:
        raise SystemExit("Close the Excel file first, then run again.") from exc


def write_result(
    test_case_id: str,
    actual: str,
    status: str,
    shot_paths: Sequence[str] | None = None,
) -> None:
    excel_path, sheet_name = _active_excel_and_sheet()
    wb = openpyxl.load_workbook(excel_path)
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
    row, columns = _find_row_and_columns(ws, test_case_id)
    if row is None:
        print(f"[!] Warning: Row for {test_case_id} not found in sheet '{ws.title}'")
        return

    shot_file = _resolve_latest_screenshot(test_case_id, shot_paths)
    target_link = os.path.abspath(shot_file) if shot_file else EVIDENCE_LINK
    display_text = os.path.basename(shot_file) if shot_file else "Evidence Doc"

    values = {
        "actual": actual,
        "status": status,
        "evidence": display_text,
        "date": datetime.now().strftime("%d-%b-%Y"),
        "tester": os.getenv("TESTER_NAME") or TESTER_NAME,
    }
    for key, col in columns.items():
        if col:
            ws.cell(row, col).value = values[key]

    if columns["evidence"] and target_link:
        cell = ws.cell(row, columns["evidence"])
        cell.value = display_text
        cell.hyperlink = target_link
        cell.style = "Hyperlink"

    wb.save(excel_path)
    print(f"Saved to: {os.path.abspath(excel_path)}  (sheet '{ws.title}', row {row})")


# =============================================================================
# 5. Unified Test Runner (called by every repXXX_*.py script)
# =============================================================================

def _parse_docstring(doc: str | None, fallback_title: str) -> tuple[str, str]:
    lines = [line.strip() for line in (doc or "").strip().splitlines() if line.strip()]
    if not lines:
        return fallback_title, fallback_title
    if lines[0].upper().startswith("REP-TC") and ":" in lines[0]:
        title = lines[0].split(":", 1)[1].strip()
    elif len(lines) > 1 and lines[0].upper().startswith("REP-TC"):
        title = lines[1]
    else:
        title = lines[0]
    return title, "\n".join(lines)


def run_report_test(
    test_case_id: str,
    route: str,
    test_fn: Callable[[ReportSession], str],
    doc: str | None = None,
    feature: str | None = None,
) -> None:
    os.chdir(PROJECT_ROOT)
    os.environ["SHEET_NAME"] = "Report"

    title, description = _parse_docstring(doc or test_fn.__doc__, test_case_id)
    reporter = create_allure_reporter()
    reporter.start_test(
        test_case_id, title, feature or title, description, f"{BASE_URL}{route}"
    )

    driver = None
    status = "failed"
    excel_status = "Fail"
    actual = ""
    shot_paths: list[str] = []
    error: BaseException | None = None

    try:
        with reporter.step(f"Validate Excel worksheet row for {test_case_id}"):
            check_excel_ready(test_case_id)

        with reporter.step("Launch Chrome WebDriver"):
            driver, wait = start_browser()

        session = ReportSession(driver, wait, reporter)
        actual = test_fn(session)
        status = "passed"
        excel_status = "Pass"

        with reporter.step("Capture passing screenshot evidence"):
            shot_paths.append(save_shot(driver, test_case_id, "report", "PASS", reporter))

    except (ReportConfigError, BlockedTest) as exc:
        error = exc
        status = "skipped"
        excel_status = "Blocked"
        actual = f"Blocked - {exc}"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "report", "BLOCKED", reporter))
            except Exception:
                pass
        reporter.attach_text(actual, "Execution prerequisite")

    except (SystemExit, SetupError, LoginError) as exc:
        error = exc
        actual = f"Setup failed - {short(exc)}"
        status = "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "setup", "FAIL", reporter))
            except Exception:
                pass
        attach_failure_diagnostics(driver, traceback.format_exc(), reporter)

    except Exception as exc:
        error = exc
        actual = short(exc)
        status = "failed" if isinstance(exc, AssertionError) else "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "report", "FAIL", reporter))
            except Exception:
                pass
        attach_failure_diagnostics(driver, traceback.format_exc(), reporter)

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            with reporter.step(f"Write '{excel_status}' result to Excel"):
                write_result(test_case_id, actual, excel_status, shot_paths=shot_paths)
        except Exception as excel_error:
            reporter.attach_text(
                f"Excel update failed: {excel_error}\n{traceback.format_exc()}",
                "Excel reporting error",
            )
            if status == "passed":
                status = "broken"
                actual += f" | Excel reporting failed: {excel_error}"

        reporter.finish(status, actual, error)

    print(f"\n{test_case_id}: {excel_status} - {actual}")
    if status in ("failed", "broken"):
        raise SystemExit(1)
    if status == "skipped":
        raise SystemExit(2)
