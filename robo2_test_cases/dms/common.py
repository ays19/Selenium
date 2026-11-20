"""
Clean POM + Allure + Excel test harness for the Robo2mation DMS test suite.

Architecture (mirrors dms/report/):
- dms_config.py     -> Loads dms/.env once, routes, directories & config validators
- allure_reporter.py -> Allure 2 lifecycle steps, screenshots & failure DOM/tracebacks
- pages/            -> Pure Selenium Page Object Model classes
- common.py         -> DmsSession facade, browser factory, Excel reporter & run_dms_test() runner
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import sys
import traceback
from typing import Callable, Sequence

# Ensure dms/ is importable regardless of working directory
DMS_DIR = Path(__file__).resolve().parent
if str(DMS_DIR) not in sys.path:
    sys.path.insert(0, str(DMS_DIR))

from allure_commons.types import AttachmentType  # noqa: E402
import openpyxl  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import (  # noqa: E402
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.remote.webdriver import WebDriver  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from allure_reporter import AllureReporter  # noqa: E402
import dms_config as cfg  # noqa: E402
from dms_config import DmsConfigError, require_env, require_other_user  # noqa: E402
from pages import (  # noqa: E402
    BulkUploadPage,
    CategorizationPage,
    DocumentViewPage,
    ExplorerPage,
    LoginError,
    LoginPage,
    MasterTablePage,
    ReviewPage,
    SetupError,
    UploadPage,
)

# Re-export convenient config constants
BASE_URL = cfg.BASE_URL
DOWNLOAD_DIR = str(cfg.DOWNLOAD_DIR)
SCREENSHOT_DIR = str(cfg.SCREENSHOT_DIR)
SAMPLE_DIR = str(cfg.SAMPLE_DIR)
EXTENSIONS = cfg.EXTENSIONS

_LAST_SAVED_SHOTS: dict[str, list[str]] = {}


class BlockedTest(RuntimeError):
    """Raised when required test configuration or accounts are missing."""


# =============================================================================
# 1. POM + Allure Test Session Facade
# =============================================================================

class DmsSession:
    """High-level POM + Allure facade passed to every DMS test scenario."""

    def __init__(self, driver: WebDriver, wait: WebDriverWait, reporter: AllureReporter):
        self.driver = driver
        self.wait = wait
        self.reporter = reporter
        self.login = LoginPage(driver, wait, cfg.BASE_URL, reporter)
        self.upload = UploadPage(driver, wait)
        self.document = DocumentViewPage(driver, wait)
        self.explorer = ExplorerPage(driver, wait)
        self.categorization = CategorizationPage(driver, wait)
        self.bulk_upload = BulkUploadPage(driver, wait)
        self.master_table = MasterTablePage(driver, wait)
        self.review = ReviewPage(driver, wait)

    def step(self, title: str):
        return self.reporter.step(title)

    def upload_document(
        self,
        ext: str = "pdf",
        doc_type: str | None = None,
        share: str | None = None,
        require_checker: bool = False,
    ) -> dict:
        with self.step(f"Upload test .{ext} document"):
            return self.upload.upload_document(
                ext=ext,
                doc_type=doc_type,
                share=share,
                require_checker=require_checker,
                approve_fn=self.review.review_document,
            )

    def new_document(self, ext: str = "pdf", doc_type: str = "1 FC Test updated/aa") -> dict:
        """Upload a fresh test document and open it in Document View."""
        info = self.upload_document(ext=ext, doc_type=doc_type)
        with self.step(f"Open document '{info['name']}' in Document View"):
            self.explorer.open_document(info["name"])
        return info

    def open_and_wait_for_ocr(self, name: str, timeout_seconds: int = 60) -> tuple[bool, str]:
        """Open `name`, wait for OCR status to become active, then return to main tab."""
        main_tab = self.driver.current_window_handle
        with self.step(f"Wait for OCR status on '{name}'"):
            self.explorer.open_document(name)
            ok, msg = self.document.wait_for_ocr_status(timeout_seconds=timeout_seconds)
            self.document.close_extra_tabs(main_tab)
        return ok, msg

    def as_other_user(self, fn: Callable):
        """Run `fn()` as OTHER_USERNAME/OTHER_PASSWORD and restore primary user."""
        return self.login.as_other_user(fn)

    def review_as_checker(self, name: str, action: str) -> tuple[bool, str]:
        """Approve or reject `name` as the second user (checker)."""
        return self.as_other_user(lambda: self.review.review_document(name, action))


# =============================================================================
# 2. Browser, Screenshot & Allure Diagnostics
# =============================================================================

def create_allure_reporter() -> AllureReporter:
    return AllureReporter(cfg.ALLURE_RESULTS_DIR)


def start_browser(timeout: int = 15) -> tuple[WebDriver, WebDriverWait]:
    options = Options()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(cfg.DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "profile.default_content_setting_values.automatic_downloads": 1,
        },
    )
    if cfg.is_headless():
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    if not cfg.is_headless():
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
    tc_folder = Path(cfg.SCREENSHOT_DIR) / tc_id
    tc_folder.mkdir(parents=True, exist_ok=True)

    file_path = (tc_folder / f"{tc_id}_{slug}_{result}.png").resolve()
    driver.save_screenshot(str(file_path))
    _LAST_SAVED_SHOTS.setdefault(tc_id, []).append(str(file_path))
    print(f"   [Screenshot saved]: {file_path}")

    if reporter and reporter.test_uuid:
        reporter.attach_file(
            file_path,
            name=f"{tc_id} ({slug} - {result}) Screenshot",
            attachment_type=AttachmentType.PNG,
        )
    return str(file_path)


def attach_failure_diagnostics(
    driver: WebDriver | None,
    test_case_id: str,
    slug: str,
    tb_text: str = "",
    reporter: AllureReporter | None = None,
) -> None:
    if driver:
        try:
            html = driver.page_source
            if reporter and reporter.test_uuid:
                reporter.attach_html(html, f"Failure DOM ({slug})")
            debug_file = cfg.DEBUG_DIR / f"{test_case_id}_{slug}.html"
            debug_file.write_text(html, encoding="utf-8")
        except Exception:
            pass
    if tb_text and reporter and reporter.test_uuid:
        reporter.attach_text(tb_text, f"Python Traceback ({slug})")


def short(error: BaseException) -> str:
    lines = str(error).splitlines()
    first = lines[0].strip()[:140] if lines else ""
    if not first:
        try:
            frames = [
                f for f in traceback.extract_tb(error.__traceback__)
                if "site-packages" not in f.filename
                and f.name not in ("run_dms_test", "<module>", "<lambda>")
            ]
            if frames:
                chain = " > ".join(f.name for f in frames)
                first = f"happened in {chain} (line {frames[-1].lineno})"
        except Exception:
            pass
    return f"{type(error).__name__}: {first}"


# =============================================================================
# 3. Excel Validation & Result Reporting
# =============================================================================

def _find_row_and_columns(ws, test_case_id: str) -> tuple[int | None, dict[str, int | None]]:
    headers: dict[int, str] = {}
    for h_row in (cfg.HEADER_ROW, 1, 2, 3, 5):
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
        "evidence": _col_of(cfg.EVIDENCE_HEADER, "remark", "evidence", "screenshot", "screen shot"),
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
        tc_folder = Path(cfg.SCREENSHOT_DIR) / tc_id
        if tc_folder.is_dir():
            pngs = sorted(tc_folder.glob("*.png"), key=lambda item: item.stat().st_mtime)
            valid = [str(p.resolve()) for p in pngs]

    if not valid:
        return None
    fail_shots = [p for p in valid if "_FAIL.png" in p]
    return fail_shots[-1] if fail_shots else valid[-1]


def check_excel_ready(test_case_id: str) -> None:
    excel_p, sheet_n = cfg.active_excel_and_sheet()
    print(f"Checking Excel: {excel_p} [Sheet: {sheet_n}] for {test_case_id}")
    wb = openpyxl.load_workbook(excel_p)
    ws = wb[sheet_n] if sheet_n in wb.sheetnames else wb.active
    row, columns = _find_row_and_columns(ws, test_case_id)
    if row is None:
        raise SetupError(f"{test_case_id} not found in column A of sheet '{ws.title}' in {excel_p}")
    missing = [k for k, v in columns.items() if v is None]
    print(f"Row {row} found in '{ws.title}'. Missing columns: {missing or 'none'}")
    try:
        with open(excel_p, "ab"):
            pass
    except PermissionError as exc:
        raise SetupError("Close the Excel file first, then run again.") from exc


def _write_row_cells(ws, row: int, columns: dict[str, int | None], actual: str, status: str, shot_file: str | None) -> None:
    target_link = os.path.abspath(shot_file) if shot_file else cfg.EVIDENCE_LINK
    display_text = os.path.basename(shot_file) if shot_file else "Evidence Doc"
    values = {
        "actual": actual,
        "status": status,
        "evidence": display_text,
        "date": datetime.now().strftime("%d-%b-%Y"),
        "tester": os.getenv("TESTER_NAME") or cfg.TESTER_NAME,
    }
    for key, col in columns.items():
        if col:
            ws.cell(row, col).value = values[key]

    if columns["evidence"] and target_link:
        cell = ws.cell(row, columns["evidence"])
        cell.value = display_text
        cell.hyperlink = target_link
        cell.style = "Hyperlink"


def write_result(
    test_case_id: str,
    actual: str,
    status: str,
    shot_paths: Sequence[str] | None = None,
) -> None:
    excel_p, sheet_n = cfg.active_excel_and_sheet()
    wb = openpyxl.load_workbook(excel_p)
    ws = wb[sheet_n] if sheet_n in wb.sheetnames else wb.active
    row, columns = _find_row_and_columns(ws, test_case_id)
    if row is None:
        print(f"[!] Warning: Row for {test_case_id} not found in sheet '{ws.title}'")
        return

    shot_file = _resolve_latest_screenshot(test_case_id, shot_paths)
    _write_row_cells(ws, row, columns, actual, status, shot_file)
    wb.save(excel_p)
    print(f"Saved to: {os.path.abspath(excel_p)}  (sheet '{ws.title}', row {row})")


def write_multi_row_results(
    test_case_id: str,
    row_entries: Sequence[tuple[str, str, str | None]],
) -> None:
    """Write consecutive Excel rows starting at `test_case_id` (used by DMS-TC032)."""
    excel_p, sheet_n = cfg.active_excel_and_sheet()
    wb = openpyxl.load_workbook(excel_p)
    ws = wb[sheet_n] if sheet_n in wb.sheetnames else wb.active
    base_row, columns = _find_row_and_columns(ws, test_case_id)
    if base_row is None:
        print(f"[!] Warning: Base row for {test_case_id} not found in sheet '{ws.title}'")
        return

    for idx, (status, actual, shot_file) in enumerate(row_entries):
        _write_row_cells(ws, base_row + idx, columns, actual, status, shot_file)

    wb.save(excel_p)
    print(f"Saved {len(row_entries)} rows from row {base_row} to: {os.path.abspath(excel_p)}")


# =============================================================================
# 4. Unified Test Runner (used by every tcXXX_*.py script)
# =============================================================================

def _parse_docstring(doc: str | None, fallback_title: str) -> tuple[str, str]:
    lines = [line.strip() for line in (doc or "").strip().splitlines() if line.strip()]
    if not lines:
        return fallback_title, fallback_title
    first = lines[0]
    if first.upper().startswith("DMS-TC") and len(lines) > 1:
        parts = first.split(None, 1)
        title = parts[1].strip() if len(parts) > 1 else lines[1]
    else:
        title = first
    return title, "\n".join(lines)


def run_dms_test(
    test_case_id: str,
    scenarios: Sequence[tuple[str, Callable[[DmsSession], tuple[bool, str]]]],
    doc: str | None = None,
    feature: str | None = None,
    required_env: Sequence[tuple[str, str]] = (),
    need_other_user: bool = False,
    multi_row: bool = False,
    summary_fn: Callable[[list[tuple[str, bool, str]]], str] | None = None,
) -> None:
    """Execute one or more DMS scenarios with POM, Allure steps/evidence, and Excel reporting."""
    os.chdir(DMS_DIR)
    os.environ.setdefault("SHEET_NAME", "DMS")

    title, description = _parse_docstring(doc, test_case_id)
    reporter = create_allure_reporter()
    reporter.start_test(test_case_id, title, feature or title, description, cfg.BASE_URL)

    driver = None
    session = None
    status = "failed"
    excel_status = "Fail"
    actual = ""
    shot_paths: list[str] = []
    failed_shots: list[str] = []
    results: list[tuple[str, bool, str]] = []
    row_entries: list[tuple[str, str, str | None]] = []
    error: BaseException | None = None

    try:
        # 1. Validate required environment variables BEFORE launching Chrome
        if need_other_user or required_env:
            with reporter.step("Validate required test configuration"):
                if need_other_user:
                    require_other_user()
                for var_name, hint in required_env:
                    require_env(var_name, hint)

        # 2. Validate Excel row & file lock BEFORE launching Chrome
        with reporter.step(f"Validate Excel worksheet row for {test_case_id}"):
            check_excel_ready(test_case_id)

        # 3. Launch browser & authenticate
        with reporter.step("Launch Chrome WebDriver"):
            driver, wait = start_browser()

        session = DmsSession(driver, wait, reporter)
        session.login.login()

        # 4. Run each scenario in its own Allure step
        for label, scenario_fn in scenarios:
            slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "step"
            ok = False
            msg = ""
            shot_file = None
            try:
                with reporter.step(label):
                    ok, msg = scenario_fn(session)
                    if not ok:
                        raise AssertionError(msg)
                shot_file = save_shot(driver, test_case_id, slug, "PASS", reporter)
                shot_paths.append(shot_file)
            except (DmsConfigError, BlockedTest):
                raise
            except (SetupError, LoginError) as setup_exc:
                error = setup_exc
                msg = str(setup_exc)
                shown = session.document.popup_text()
                if shown and shown.lower() not in msg.lower():
                    msg += f" - page said: {shown}"
                shot_file = save_shot(driver, test_case_id, slug, "FAIL", reporter)
                shot_paths.append(shot_file)
                failed_shots.append(shot_file)
                attach_failure_diagnostics(driver, test_case_id, slug, traceback.format_exc(), reporter)
                row_entries.append(("Fail", msg, shot_file))
                raise SetupError(f"{label}: {msg}") from setup_exc
            except AssertionError as assert_exc:
                error = assert_exc
                ok, msg = False, str(assert_exc)
                shown = session.document.popup_text()
                if shown and shown.lower() not in msg.lower():
                    msg += f" - page said: {shown}"
                shot_file = save_shot(driver, test_case_id, slug, "FAIL", reporter)
                shot_paths.append(shot_file)
                failed_shots.append(shot_file)
                attach_failure_diagnostics(driver, test_case_id, slug, traceback.format_exc(), reporter)
            except Exception as exc:
                error = exc
                status = "broken"
                ok, msg = False, short(exc)
                shown = session.document.popup_text()
                if shown and shown.lower() not in msg.lower():
                    msg += f" - page said: {shown}"
                shot_file = save_shot(driver, test_case_id, slug, "FAIL", reporter)
                shot_paths.append(shot_file)
                failed_shots.append(shot_file)
                attach_failure_diagnostics(driver, test_case_id, slug, traceback.format_exc(), reporter)

            print(f"{label:28} -> {'PASS' if ok else 'FAIL'} ({msg})")
            results.append((label, ok, msg))
            row_entries.append(("Pass" if ok else "Fail", msg, shot_file))

        if all(ok for _, ok, _ in results):
            status = "passed"
            excel_status = "Pass"
        else:
            excel_status = "Fail"
            if status != "broken":
                status = "failed"

        if summary_fn is not None:
            actual = summary_fn(results)
        elif len(results) == 1:
            actual = results[0][2]
        else:
            actual = ". ".join(
                f"{lbl}: {'OK' if ok else 'FAILED'} - {msg}" for lbl, ok, msg in results
            )

    except (DmsConfigError, BlockedTest) as exc:
        error = exc
        status = "skipped"
        excel_status = "Blocked"
        actual = f"Blocked - {exc}"
        reporter.attach_text(actual, "Execution prerequisite")

    except (SetupError, LoginError, SystemExit) as exc:
        error = exc
        status = "broken"
        excel_status = "Fail"
        actual = f"Setup Error - {exc}"
        if driver and not failed_shots:
            try:
                shot_file = save_shot(driver, test_case_id, "setup", "FAIL", reporter)
                failed_shots.append(shot_file)
                attach_failure_diagnostics(driver, test_case_id, "setup", traceback.format_exc(), reporter)
            except Exception:
                pass

    except Exception as exc:
        error = exc
        status = "broken"
        excel_status = "Fail"
        actual = short(exc)
        if driver:
            try:
                shot_file = save_shot(driver, test_case_id, "error", "FAIL", reporter)
                failed_shots.append(shot_file)
                attach_failure_diagnostics(driver, test_case_id, "error", traceback.format_exc(), reporter)
            except Exception:
                pass

    finally:
        if session is not None:
            try:
                session.categorization.cleanup_created_items()
            except Exception:
                pass
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        try:
            with reporter.step(f"Write '{excel_status}' result to Excel"):
                if multi_row and row_entries:
                    write_multi_row_results(test_case_id, row_entries)
                else:
                    chosen_shots = failed_shots if failed_shots else shot_paths
                    write_result(test_case_id, actual, excel_status, shot_paths=chosen_shots)
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
