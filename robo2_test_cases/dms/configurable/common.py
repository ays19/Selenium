"""Shared runner, POM session, Allure writer (no pytest), and Excel updater for Configurable tests."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
import traceback
from typing import Callable
import uuid

import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# Ensure both dms/ and dms/configurable/ are importable regardless of working directory
CONFIGURABLE_DIR = Path(__file__).resolve().parent
DMS_DIR = CONFIGURABLE_DIR.parent
for _path in (str(CONFIGURABLE_DIR), str(DMS_DIR)):
    if _path not in sys.path:
        sys.path.append(_path)

from configurable import configurable_config as cfg  # noqa: E402
from configurable.pages.login_page import LoginPage  # noqa: E402
from configurable.pages.user_management_page import UserManagementPage  # noqa: E402

ALLURE_DIR = cfg.ALLURE_RESULTS_DIR
SHEET_NAME = cfg.SHEET_NAME


class AllureStandaloneWriter:
    """Writes Allure 2 JSON result files without requiring pytest."""

    def __init__(self, test_id: str, name: str, description: str) -> None:
        ALLURE_DIR.mkdir(parents=True, exist_ok=True)
        self.uuid = str(uuid.uuid4())
        self.test_id = test_id
        self.name = name
        self.description = description
        self.start_ms = int(time.time() * 1000)
        self.steps: list[dict] = []
        self.attachments: list[dict] = []

    @contextmanager
    def step(self, title: str):
        step_obj = {
            "name": title,
            "status": "passed",
            "start": int(time.time() * 1000),
            "stop": 0,
        }
        try:
            yield
        except Exception as exc:
            step_obj["status"] = "failed"
            step_obj["statusDetails"] = {"message": str(exc)}
            raise
        finally:
            step_obj["stop"] = int(time.time() * 1000)
            self.steps.append(step_obj)

    def attach_png(self, png_path: Path, label: str = "Screenshot") -> None:
        if not png_path.is_file():
            return
        target_name = f"{uuid.uuid4()}-attachment.png"
        (ALLURE_DIR / target_name).write_bytes(png_path.read_bytes())
        self.attachments.append({"name": label, "source": target_name, "type": "image/png"})

    def finalize(self, status: str, message: str = "", trace: str = "") -> None:
        payload = {
            "uuid": self.uuid,
            "name": f"{self.test_id}: {self.name}",
            "fullName": f"configurable.{self.test_id}",
            "description": self.description,
            "status": status.lower(),
            "statusDetails": {"message": message, "trace": trace} if message else {},
            "steps": self.steps,
            "attachments": self.attachments,
            "start": self.start_ms,
            "stop": int(time.time() * 1000),
            "labels": [
                {"name": "suite", "value": "Configurable Sanity Suite"},
                {"name": "feature", "value": "User Management & Access Controls"},
            ],
        }
        out = ALLURE_DIR / f"{self.uuid}-result.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class ConfigurableSession:
    """High-level POM facade mirrored after ReportSession."""

    def __init__(self, driver: webdriver.Chrome, wait: WebDriverWait, allure_writer: AllureStandaloneWriter):
        self.driver = driver
        self.wait = wait
        self.allure = allure_writer
        self.base_url = cfg.base_url()
        self.login_page = LoginPage(driver, wait)
        self.user_page = UserManagementPage(driver, wait)
        self.current_role: str | None = None

    def step(self, title: str):
        return self.allure.step(title)

    def login_as_role(self, role: str) -> None:
        profile = cfg.get_profile(role)
        with self.step(f"Login as role '{role}' ({profile.username})"):
            if self.current_role is not None:
                self.login_page.logout_if_needed(self.base_url)
            self.login_page.login_expect_success(self.base_url, profile.username, profile.password)
            self.current_role = role

    def open_route(self, route: str) -> None:
        with self.step(f"Open route: {route}"):
            self.user_page.open(self.base_url, route)


def _build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--disable-notifications")
    if cfg.is_headless():
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
    else:
        opts.add_argument("--start-maximized")
    prefs = {
        "download.default_directory": str(cfg.download_dir()),
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "safebrowsing.enabled": True,
    }
    opts.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=opts)


def _save_evidence(driver: webdriver.Chrome, test_case_id: str, suffix: str) -> Path:
    folder = cfg.evidence_dir() / test_case_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{test_case_id}_configurable_{suffix}.png"
    driver.save_screenshot(str(path))
    print(f"   [Screenshot saved]: {path}")
    return path


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
            if not kw:
                continue
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

    target_id = str(test_case_id).strip().casefold()
    target_row = next(
        (
            r for r in range(1, ws.max_row + 1)
            if str(ws.cell(r, 1).value or "").strip().casefold() == target_id
        ),
        None,
    )
    return target_row, columns


def _update_excel(
    test_case_id: str,
    status: str,
    actual_result: str,
    shot_path: Path | None = None,
) -> None:
    wb_path, sheet_name = cfg.active_excel_and_sheet()
    print(f"Checking Excel: {wb_path} [Sheet: {sheet_name}] for {test_case_id}")
    try:
        wb = openpyxl.load_workbook(wb_path)
    except PermissionError as exc:
        print(f"[!] Excel update skipped (close workbook to save): {exc}")
        return

    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
    row_idx, columns = _find_row_and_columns(ws, test_case_id)
    if row_idx is None:
        print(f"Warning: {test_case_id} not found in sheet '{ws.title}'.")
        return

    shot_file = str(shot_path.resolve()) if shot_path and shot_path.is_file() else ""
    target_link = shot_file or cfg.EVIDENCE_LINK
    display_text = shot_path.name if shot_file and shot_path else "Evidence Doc"

    values = {
        "actual": actual_result[:500],
        "status": status,
        "evidence": display_text,
        "date": datetime.now().strftime("%d-%b-%Y"),
        "tester": os.getenv("TESTER_NAME") or cfg.TESTER_NAME,
    }
    for key, col in columns.items():
        if col:
            ws.cell(row=row_idx, column=col, value=values[key])

    if columns["evidence"] and target_link:
        cell = ws.cell(row=row_idx, column=columns["evidence"])
        cell.value = display_text
        cell.hyperlink = target_link
        cell.style = "Hyperlink"

    try:
        wb.save(wb_path)
        print(f"Saved to: {wb_path} (sheet '{ws.title}', row {row_idx})")
    except PermissionError as exc:
        print(f"[!] Excel save skipped (file is locked/open): {exc}")


def run_configurable_test(
    test_case_id: str,
    route: str,
    test_fn: Callable[[ConfigurableSession], str],
    docstring: str | None = "",
) -> None:
    os.chdir(CONFIGURABLE_DIR)
    os.environ.setdefault("SHEET_NAME", cfg.SHEET_NAME)

    title = (docstring or test_case_id).strip().splitlines()[0]
    allure_writer = AllureStandaloneWriter(test_case_id, title, docstring or "")
    driver = _build_driver()
    wait = WebDriverWait(driver, 15)
    session = ConfigurableSession(driver, wait, allure_writer)

    passed = False
    try:
        actual = test_fn(session)
        shot = _save_evidence(driver, test_case_id, "PASS")
        allure_writer.attach_png(shot, "Pass Evidence")
        allure_writer.finalize("passed", actual)
        _update_excel(test_case_id, "Pass", actual, shot_path=shot)
        print(f"\n{test_case_id}: Pass - {actual}")
        passed = True
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {exc}"
        shot = _save_evidence(driver, test_case_id, "FAIL")
        allure_writer.attach_png(shot, "Failure Screenshot")
        allure_writer.finalize("failed", err_msg, traceback.format_exc())
        _update_excel(test_case_id, "Fail", err_msg, shot_path=shot)
        print(f"\n{test_case_id}: Fail - {err_msg}")
    finally:
        driver.quit()

    if not passed:
        raise SystemExit(1)
