"""
Industry-standard POM + Allure + Excel foundation for the Robo2mation Report suite.
- Pure Python, Selenium WebDriver, OpenPyXL, and allure-python-commons (no pytest).
- Provides:
    * LoginPage(BasePage): POM authentication and session switching
    * ReportSession: High-level POM + Allure facade for concise, readable test scripts
    * BrowserManager, EvidenceManager, ExcelReporter
    * run_report_test(): Standardized test runner (parses docstring, runs POM, updates Excel & Allure)
"""
from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime
import os
from pathlib import Path
import sys
import traceback
from typing import Callable, Sequence

# Ensure both `dms/` and `dms/report/` are importable regardless of working directory
REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
for _p in (str(REPORT_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from allure_commons.types import AttachmentType  # noqa: E402
from allure_commons.utils import uuid4  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
import openpyxl  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.common.keys import Keys  # noqa: E402
from selenium.webdriver.remote.webdriver import WebDriver  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from report.allure_reporter import AllureReporter  # noqa: E402
from report.pages.base_page import BasePage  # noqa: E402
from report.pages.report_page import ReportPage  # noqa: E402
from report.pages.requested_downloads_page import RequestedDownloadsPage  # noqa: E402
from report.report_config import (  # noqa: E402
    ReportConfigError,
    expected_value,
    filter_values,
    get_profile,
)


# ---------------------------------------------------------------------------
# 1. Environment & Directory Configuration
# ---------------------------------------------------------------------------
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(REPORT_DIR / ".env.report", override=False)

BASE_URL: str = (os.getenv("BASE_URL") or "").rstrip("/")
USERNAME: str = os.getenv("REPORT_USERNAME") or os.getenv("DMS_USERNAME") or ""
PASSWORD: str = os.getenv("REPORT_PASSWORD") or os.getenv("DMS_PASSWORD") or ""
TESTER_NAME: str = os.getenv("TESTER_NAME") or ""
SHEET_NAME: str = os.getenv("SHEET_NAME", "Report")
EXCEL_PATH: str = os.getenv("EXCEL_PATH") or ""
EVIDENCE_LINK: str = os.getenv("EVIDENCE_LINK") or ""
EVIDENCE_HEADER: str = os.getenv("EVIDENCE_HEADER", "remark").lower()
HEADER_ROW: int = 4


def _resolve_dir(env_key: str, default_name: str) -> Path:
    raw = os.getenv(env_key, default_name)
    path = Path(raw)
    resolved = path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


SCREENSHOT_DIR: str = str(_resolve_dir("SCREENSHOT_DIR", "screenshots"))
DOWNLOAD_DIR: str = str(_resolve_dir("DOWNLOAD_DIR", "downloads"))
ALLURE_RESULTS_DIR: Path = _resolve_dir("REPORT_ALLURE_RESULTS_DIR", "allure-results")
REQUESTED_DOWNLOAD_URL: str = f"{BASE_URL}/requested_downloads/view/"


class SetupError(RuntimeError):
    """Raised when login, browser initialization, or test setup fails."""


class BlockedTest(RuntimeError):
    """Raised when required role credentials or sentinel test data are missing in .env.report."""


# Active AllureReporter context so POM classes and helpers can log steps/attachments
_ACTIVE_REPORTER: AllureReporter | None = None


def set_active_reporter(reporter: AllureReporter | None) -> None:
    global _ACTIVE_REPORTER
    _ACTIVE_REPORTER = reporter


def get_active_reporter() -> AllureReporter | None:
    return _ACTIVE_REPORTER


def allure_step(title: str):
    """Context manager that records an Allure step if a reporter is active."""
    if _ACTIVE_REPORTER and _ACTIVE_REPORTER.test_uuid:
        return _ACTIVE_REPORTER.step(title)
    return nullcontext()


# ---------------------------------------------------------------------------
# 2. Page Object Model: LoginPage (with Allure Step Integration)
# ---------------------------------------------------------------------------
class LoginPage(BasePage):
    """Page Object encapsulating Robo2mation authentication and session management."""

    USERNAME_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Username')]")
    PASSWORD_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Password')]")
    MESSAGE_SELECTORS = (
        ".toast, .alert, .swal2-popup, [role='alert'], .snackbar, "
        ".Toastify__toast, .ant-message, .growl-animated, [data-notify]"
    )
    LOGOUT_ROUTE = "/login/logout/"

    def __init__(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        base_url: str = BASE_URL,
        reporter: AllureReporter | None = None,
    ):
        super().__init__(driver, wait)
        self.base_url = (base_url or BASE_URL).rstrip("/")
        self.reporter = reporter or _ACTIVE_REPORTER

    def _step(self, title: str):
        active = self.reporter or _ACTIVE_REPORTER
        if active and active.test_uuid:
            return active.step(title)
        return nullcontext()

    def is_login_page_displayed(self, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.USERNAME_INPUT)
            )
            return True
        except TimeoutException:
            return False

    def clear_session(self) -> None:
        with self._step("Clear browser cookies and storage"):
            try:
                self.driver.delete_all_cookies()
            except Exception:
                pass
            try:
                self.driver.execute_script(
                    "window.localStorage.clear(); window.sessionStorage.clear();"
                )
            except Exception:
                pass

    def get_popup_message(self) -> str:
        messages: list[str] = []
        for elem in self.visible_elements(By.CSS_SELECTOR, self.MESSAGE_SELECTORS):
            try:
                text = elem.text.strip()
                if text:
                    messages.append(text)
            except StaleElementReferenceException:
                continue
        return " | ".join(messages)

    def login_as(self, username: str, password: str) -> None:
        if not self.base_url:
            raise SetupError("BASE_URL is not configured in .env.")

        with self._step(f"Sign in as user '{username}'"):
            self.driver.get(self.base_url)
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

            user_field = self.wait.until(
                EC.visibility_of_element_located(self.USERNAME_INPUT)
            )
            user_field.clear()
            user_field.send_keys(username)

            pass_field = self.driver.find_element(*self.PASSWORD_INPUT)
            pass_field.clear()
            pass_field.send_keys(password, Keys.ENTER)

            try:
                self.wait.until(EC.invisibility_of_element_located(self.USERNAME_INPUT))
            except TimeoutException as exc:
                popup = self.get_popup_message() or "no error banner shown"
                raise SetupError(
                    f"Login as '{username}' failed (still on login page). "
                    f"Verify credentials in report/.env.report. Page message: {popup}"
                ) from exc

    def logout(self) -> None:
        with self._step("Log out of current session"):
            self.driver.get(f"{self.base_url}{self.LOGOUT_ROUTE}")
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

    def switch_user(self, username: str, password: str) -> None:
        with self._step(f"Switch user session to '{username}'"):
            self.logout()
            self.login_as(username, password)


# ---------------------------------------------------------------------------
# 3. High-Level POM + Allure Session Facade (Keeps Test Scripts Ultra-Clean)
# ---------------------------------------------------------------------------
class ReportSession:
    """
    Combines LoginPage, ReportPage, RequestedDownloadsPage, and AllureReporter
    into one cohesive POM interface so each repXXX_*.py test script is concise,
    self-documenting, and reusable.
    """

    def __init__(self, driver: WebDriver, wait: WebDriverWait, reporter: AllureReporter):
        self.driver = driver
        self.wait = wait
        self.reporter = reporter
        self.login_page = LoginPage(driver, wait, BASE_URL, reporter)
        self.report_page = ReportPage(driver, wait)
        self.downloads_page = RequestedDownloadsPage(driver, wait)
        self._logged_in = False
        self.current_role = ""

    def step(self, title: str):
        return self.reporter.step(title)

    def login_as_role(self, role_key: str) -> str:
        """Sign in (or switch session) using a role key from report/.env.report."""
        profile = get_profile(role_key)
        if self._logged_in:
            self.login_page.switch_user(profile.username, profile.password)
        else:
            self.login_page.login_as(profile.username, profile.password)
            self._logged_in = True
        self.current_role = role_key
        return profile.username

    def open_report(self, route: str, check_accessible: bool = True) -> None:
        """Navigate to the report route and optionally verify the table is accessible."""
        with self.step(f"Open report page ({route})"):
            self.report_page.open(BASE_URL, route)
            if check_accessible:
                self.report_page.assert_accessible()

    def verify_scope(self, visibility: str, role_key: str = "") -> str:
        """
        Verify role-based data visibility ('own', 'all', 'related', 'department', 'denied', 'accessible').
        """
        role = (role_key or self.current_role).upper()
        with self.step(f"Verify report visibility scope: '{visibility}'"):
            if visibility == "denied":
                self.report_page.assert_denied()
                return f"Role '{role.lower()}': access denied as expected."

            self.report_page.assert_accessible()
            if visibility == "accessible":
                return f"Role '{role.lower()}': report is accessible and table loaded."

            key_map = {
                "own": "REPORT_EXPECTED_OWN_TEXT",
                "all": "REPORT_EXPECTED_OTHER_TEXT",
                "related": "REPORT_EXPECTED_RELATED_TEXT",
                "department": "REPORT_EXPECTED_DEPARTMENT_TEXT",
            }
            base_key = key_map.get(visibility)
            if not base_key:
                return f"Role '{role.lower()}': report access verified."

            expected = expected_value(f"{base_key}_{role}") or expected_value(base_key)
            if not expected:
                raise BlockedTest(
                    f"Set {base_key}_{role} (or {base_key}) in report/.env.report to verify '{visibility}' scope."
                )

            self.report_page.assert_table_contains(expected, f"{visibility}-scope record")

            if visibility == "own":
                other = (
                    expected_value(f"REPORT_EXPECTED_OTHER_TEXT_{role}")
                    or expected_value("REPORT_EXPECTED_OTHER_TEXT")
                )
                if not other:
                    raise BlockedTest(
                        f"Set REPORT_EXPECTED_OTHER_TEXT in report/.env.report to verify restricted rows."
                    )
                self.report_page.assert_table_not_contains(other, "another user's record")
                return f"Role '{role.lower()}': sees own record ('{expected}') and cannot see '{other}'."

            return f"Role '{role.lower()}': verified '{visibility}' record ('{expected}')."

    def search_or_filter(self, labels: list[str], expected_key: str = "REPORT_EXPECTED_FILTER_TEXT") -> str:
        """Apply search or filter fields and verify expected result row."""
        with self.step(f"Search/Filter report by: {', '.join(labels)}"):
            self.report_page.apply_label_filters(
                labels=labels,
                values=filter_values(),
                expected_text=expected_value(expected_key),
            )
        return f"Searched/Filtered by {', '.join(labels)} and verified matching rows."

    def filter_by_date(self, expected_key: str = "REPORT_EXPECTED_DATE_TEXT") -> str:
        """Apply configured date range from .env.report and verify matching row."""
        date_from = expected_value("REPORT_DATE_FROM")
        date_to = expected_value("REPORT_DATE_TO")
        expected_row = expected_value(expected_key)
        if not date_from or not date_to or not expected_row:
            raise BlockedTest(
                "Set REPORT_DATE_FROM, REPORT_DATE_TO, and REPORT_EXPECTED_DATE_TEXT in report/.env.report."
            )
        with self.step(f"Filter by date range ({date_from} to {date_to})"):
            self.report_page.apply_date_range(date_from, date_to, expected_row)
        return f"Applied date range ({date_from} to {date_to}) and verified '{expected_row}'."

    def sort_by(self, columns: list[str]) -> str:
        """Sort report table by each column in `columns`."""
        with self.step(f"Sort report columns: {', '.join(columns)}"):
            self.report_page.sort_columns(columns)
        return f"Verified sorting on columns: {', '.join(columns)}."

    def export(
        self,
        actions: list[str],
        page_sizes: Sequence[str] = (),
        requested_download: bool = False,
    ) -> str:
        """Execute Copy/CSV/Excel/Print export controls and optionally verify Requested Downloads."""
        download_dir = Path(DOWNLOAD_DIR)
        if page_sizes:
            with self.step(f"Test page sizes: {', '.join(page_sizes)}"):
                for size in page_sizes:
                    self.report_page.choose_page_size(size.strip())

        downloaded: list[Path] = []
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
                        downloaded.append(
                            self.report_page.wait_for_download(
                                download_dir,
                                before,
                                ext,
                                timeout=12 if requested_download else 30,
                            )
                        )
                    except TimeoutError:
                        if not requested_download:
                            raise
                elif action.casefold() == "print":
                    self.wait.until(
                        lambda d: bool(
                            d.execute_script("return window.__reportPrintCalled === true")
                        )
                    )
                elif action.casefold() == "copy":
                    self.report_page.assert_accessible()

        if requested_download:
            with self.step("Verify entry in Requested Downloads page"):
                self.downloads_page.open(REQUESTED_DOWNLOAD_URL)
                self.downloads_page.assert_download_request_visible(
                    expected_value("REPORT_EXPECTED_DOWNLOAD_TEXT")
                )

        files_info = f" Downloaded: {', '.join(p.name for p in downloaded)}." if downloaded else ""
        req_info = " Verified in Requested Downloads." if requested_download else ""
        return f"Completed export actions ({', '.join(actions)}).{files_info}{req_info}"


# ---------------------------------------------------------------------------
# 4. WebDriver Factory (BrowserManager)
# ---------------------------------------------------------------------------
class BrowserManager:
    """Creates and configures a Chrome WebDriver instance for Report tests."""

    @staticmethod
    def create_driver(
        download_dir: str = DOWNLOAD_DIR,
        timeout: int = 15,
    ) -> tuple[WebDriver, WebDriverWait]:
        with allure_step("Launch Chrome WebDriver"):
            options = Options()
            options.add_experimental_option(
                "prefs",
                {
                    "download.default_directory": os.path.abspath(download_dir),
                    "download.prompt_for_download": False,
                    "profile.default_content_setting_values.automatic_downloads": 1,
                },
            )
            driver = webdriver.Chrome(options=options)
            driver.maximize_window()
            wait = WebDriverWait(
                driver,
                timeout,
                ignored_exceptions=(
                    NoSuchElementException,
                    StaleElementReferenceException,
                ),
            )
            return driver, wait


# ---------------------------------------------------------------------------
# 5. Screenshot & Allure Evidence Manager (No debug/ disk clutter)
# ---------------------------------------------------------------------------
class EvidenceManager:
    """Saves screenshots for Excel hyperlinks and attaches evidence directly to Allure."""

    def __init__(self, screenshot_dir: str = SCREENSHOT_DIR):
        self.screenshot_dir = Path(screenshot_dir).resolve()
        self.saved_shots: dict[str, list[str]] = {}

    def save_screenshot(
        self,
        driver: WebDriver,
        test_case_id: str,
        slug: str,
        result: str,
        attach_to_allure: bool = True,
    ) -> str:
        tc_id = str(test_case_id).strip()
        tc_folder = self.screenshot_dir / tc_id
        tc_folder.mkdir(parents=True, exist_ok=True)

        file_path = (tc_folder / f"{tc_id}_{slug}_{result}.png").resolve()
        driver.save_screenshot(str(file_path))
        self.saved_shots.setdefault(tc_id, []).append(str(file_path))
        print(f"   [Screenshot saved]: {file_path}")

        if attach_to_allure and _ACTIVE_REPORTER and _ACTIVE_REPORTER.test_uuid:
            _ACTIVE_REPORTER.attach_file(
                file_path,
                name=f"{tc_id} ({result}) Screenshot",
                attachment_type=AttachmentType.PNG,
            )
        return str(file_path)

    @staticmethod
    def attach_failure_diagnostics(driver: WebDriver | None, tb_text: str = "") -> None:
        """Attach DOM HTML and traceback directly to Allure in-memory (no debug/ folder)."""
        if not (_ACTIVE_REPORTER and _ACTIVE_REPORTER.test_uuid):
            return
        if driver:
            try:
                _ACTIVE_REPORTER.lifecycle.attach_data(
                    uuid4(),
                    driver.page_source,
                    name="Failure Page DOM (HTML)",
                    attachment_type=AttachmentType.HTML,
                    parent_uuid=_ACTIVE_REPORTER.test_uuid,
                )
            except Exception:
                pass
        if tb_text:
            _ACTIVE_REPORTER.attach_text(tb_text, "Python Traceback")

    def resolve_latest_screenshot(
        self,
        test_case_id: str,
        shot_paths: Sequence[str] | None = None,
    ) -> str | None:
        tc_id = str(test_case_id).strip()
        candidates = list(shot_paths or []) or list(self.saved_shots.get(tc_id, []))
        valid = [str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()]

        if not valid:
            tc_folder = self.screenshot_dir / tc_id
            if tc_folder.is_dir():
                pngs = sorted(
                    tc_folder.glob("*.png"),
                    key=lambda item: item.stat().st_mtime,
                )
                valid = [str(p.resolve()) for p in pngs]

        if not valid:
            return None

        fail_shots = [p for p in valid if "_FAIL.png" in p]
        return fail_shots[-1] if fail_shots else valid[-1]


# ---------------------------------------------------------------------------
# 6. Excel Reporter (with Allure Step Integration & Screenshot Hyperlinking)
# ---------------------------------------------------------------------------
class ExcelReporter:
    """Validates and updates the Report sheet in the Excel workbook with screenshot links."""

    def __init__(self, evidence_manager: EvidenceManager):
        self.evidence = evidence_manager

    @staticmethod
    def get_active_excel_and_sheet() -> tuple[str, str]:
        raw_excel = os.environ.get("EXCEL_PATH") or EXCEL_PATH
        if not raw_excel:
            raise SystemExit("EXCEL_PATH is not set in .env or environment.")
        excel_path = Path(raw_excel)
        if not excel_path.is_absolute():
            excel_path = (PROJECT_ROOT / excel_path).resolve()
        sheet_name = os.environ.get("SHEET_NAME") or SHEET_NAME or "Report"
        return str(excel_path), sheet_name

    @staticmethod
    def find_row_and_columns(
        ws, test_case_id: str
    ) -> tuple[int | None, dict[str, int | None]]:
        headers: dict[int, str] = {}
        for h_row in (HEADER_ROW, 1, 2, 3, 5):
            for col in range(1, ws.max_column + 1):
                text = str(ws.cell(h_row, col).value or "").strip().lower()
                if text:
                    headers[col] = text
            if any("status" in t or "actual" in t for t in headers.values()):
                break
            headers.clear()

        def col_of(*keywords: str) -> int | None:
            for kw in keywords:
                for col, text in headers.items():
                    if kw in text:
                        return col
            return None

        columns = {
            "actual": col_of("actual"),
            "status": col_of("status"),
            "evidence": col_of(
                EVIDENCE_HEADER, "remark", "evidence", "screenshot", "screen shot"
            ),
            "date": col_of("date"),
            "tester": col_of("tester"),
        }

        target_id = str(test_case_id).strip().lower()
        target_row = None
        for row_idx in range(1, ws.max_row + 1):
            cell_val = str(ws.cell(row_idx, 1).value or "").strip().lower()
            if cell_val == target_id:
                target_row = row_idx
                break

        return target_row, columns

    def check_ready(self, test_case_id: str) -> None:
        with allure_step(f"Validate Excel worksheet row for {test_case_id}"):
            excel_path, sheet_name = self.get_active_excel_and_sheet()
            print(
                f"Checking Excel: {excel_path} [Sheet: {sheet_name}] for {test_case_id}"
            )
            wb = openpyxl.load_workbook(excel_path)
            ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
            row, columns = self.find_row_and_columns(ws, test_case_id)
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
        self,
        test_case_id: str,
        actual: str,
        status: str,
        shot_paths: Sequence[str] | None = None,
    ) -> None:
        with allure_step(f"Write '{status}' result & screenshot link to Excel"):
            excel_path, sheet_name = self.get_active_excel_and_sheet()
            wb = openpyxl.load_workbook(excel_path)
            ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
            row, columns = self.find_row_and_columns(ws, test_case_id)
            if row is None:
                print(
                    f"[!] Warning: Row for {test_case_id} not found in sheet '{ws.title}'"
                )
                return

            shot_file = self.evidence.resolve_latest_screenshot(
                test_case_id, shot_paths
            )
            if shot_file:
                target_link = os.path.abspath(shot_file)
                display_text = os.path.basename(shot_file)
            else:
                target_link = EVIDENCE_LINK
                display_text = "Evidence Doc"

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
            print(
                f"Saved to: {os.path.abspath(excel_path)}  (sheet '{ws.title}', row {row})"
            )


# ---------------------------------------------------------------------------
# 7. Public Facade & Unified POM Test Runner
# ---------------------------------------------------------------------------
evidence_manager = EvidenceManager()
excel_reporter = ExcelReporter(evidence_manager)


def create_allure_reporter() -> AllureReporter:
    reporter = AllureReporter(ALLURE_RESULTS_DIR)
    set_active_reporter(reporter)
    return reporter


def short(error: BaseException) -> str:
    lines = str(error).splitlines()
    first = lines[0].strip()[:140] if lines else ""
    if not first:
        try:
            frames = [
                f
                for f in traceback.extract_tb(error.__traceback__)
                if "site-packages" not in f.filename
                and f.name not in ("run_report_case", "run_report_test", "<module>", "<lambda>")
            ]
            if frames:
                chain = " > ".join(f.name for f in frames)
                first = f"happened in {chain} (line {frames[-1].lineno})"
        except Exception:
            pass
    return f"{type(error).__name__}: {first}"


def start_browser() -> tuple[WebDriver, WebDriverWait]:
    return BrowserManager.create_driver()


def login_as(driver: WebDriver, wait: WebDriverWait, username: str, password: str) -> None:
    LoginPage(driver, wait).login_as(username, password)


def logout(driver: WebDriver, wait: WebDriverWait | None = None) -> None:
    effective_wait = wait or WebDriverWait(driver, 5)
    LoginPage(driver, effective_wait).logout()


def save_shot(
    driver: WebDriver,
    test_case_id: str,
    slug: str,
    result: str,
    attach_to_allure: bool = True,
) -> str:
    return evidence_manager.save_screenshot(
        driver, test_case_id, slug, result, attach_to_allure=attach_to_allure
    )


def attach_failure_diagnostics(driver: WebDriver | None, tb_text: str = "") -> None:
    evidence_manager.attach_failure_diagnostics(driver, tb_text)


def check_excel_ready(test_case_id: str) -> None:
    excel_reporter.check_ready(test_case_id)


def write_result(
    test_case_id: str,
    actual: str,
    status: str,
    shot_paths: Sequence[str] | None = None,
) -> None:
    excel_reporter.write_result(test_case_id, actual, status, shot_paths=shot_paths)


def _parse_docstring(doc: str | None, fallback_title: str) -> tuple[str, str]:
    """Extract (feature_title, full_description) from the test script's docstring."""
    lines = [line.strip() for line in (doc or "").strip().splitlines() if line.strip()]
    if not lines:
        return fallback_title, fallback_title
    # If line 0 is TEST_CASE_ID (like 'REP-TC001'), line 1 is the Feature Title
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
    """
    Execute a single Report test script using ReportSession (POM + Allure + Excel).
    `test_fn(session)` receives a ready `ReportSession` instance and returns the Actual Result text.
    """
    os.chdir(PROJECT_ROOT)
    os.environ["SHEET_NAME"] = "Report"

    title, description = _parse_docstring(doc or test_fn.__doc__, test_case_id)
    feature_name = feature or title

    reporter = create_allure_reporter()
    report_url = f"{BASE_URL}{route}"
    reporter.start_test(test_case_id, title, feature_name, description, report_url)

    driver = None
    wait = None
    status = "failed"
    excel_status = "Fail"
    actual = ""
    shot_paths: list[str] = []
    error: BaseException | None = None

    try:
        check_excel_ready(test_case_id)
        driver, wait = start_browser()
        session = ReportSession(driver, wait, reporter)

        actual = test_fn(session)
        status = "passed"
        excel_status = "Pass"

        with reporter.step("Capture passing screenshot evidence"):
            shot_paths.append(save_shot(driver, test_case_id, "report", "PASS"))

    except (ReportConfigError, BlockedTest) as exc:
        error = exc
        status = "skipped"
        excel_status = "Blocked"
        actual = f"Blocked - {exc}"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "report", "BLOCKED"))
            except Exception:
                pass
        reporter.attach_text(actual, "Execution prerequisite")

    except (SystemExit, SetupError) as exc:
        error = exc
        actual = f"Setup failed - {short(exc)}"
        status = "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "setup", "FAIL"))
            except Exception:
                pass
        attach_failure_diagnostics(driver, traceback.format_exc())

    except Exception as exc:
        error = exc
        actual = short(exc)
        status = "failed" if isinstance(exc, AssertionError) else "broken"
        excel_status = "Fail"
        if driver:
            try:
                shot_paths.append(save_shot(driver, test_case_id, "report", "FAIL"))
            except Exception:
                pass
        attach_failure_diagnostics(driver, traceback.format_exc())

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
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
        set_active_reporter(None)

    print(f"\n{test_case_id}: {excel_status} - {actual}")
    if status in ("failed", "broken"):
        raise SystemExit(1)
    if status == "skipped":
        raise SystemExit(2)