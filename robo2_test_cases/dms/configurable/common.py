"""Shared runner, POM session, Allure writer (no pytest), and Excel updater for Configurable tests."""
from __future__ import annotations

import json
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import openpyxl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# Ensure dms/ is importable so report.pages.base_page can be reused cleanly
DMS_DIR = Path(__file__).resolve().parents[1]
if str(DMS_DIR) not in sys.path:
    sys.path.insert(0, str(DMS_DIR))

import configurable_config as cfg
from pages.login_page import LoginPage
from pages.user_management_page import UserManagementPage

ALLURE_DIR = DMS_DIR / "allure-results"
SHEET_NAME = "Configurable"


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
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    prefs = {
        "download.default_directory": str(cfg.download_dir()),
        "download.prompt_for_download": False,
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


def _update_excel(test_case_id: str, status: str, actual_result: str) -> None:
    wb_path = cfg.excel_path()
    print(f"Checking Excel: {wb_path} [Sheet: {SHEET_NAME}] for {test_case_id}")
    wb = openpyxl.load_workbook(wb_path)
    ws = wb[SHEET_NAME]
    for row_idx in range(5, ws.max_row + 1):
        cell_val = str(ws.cell(row=row_idx, column=1).value or "").strip()
        if cell_val == test_case_id:
            ws.cell(row=row_idx, column=5, value=actual_result[:500])
            ws.cell(row=row_idx, column=6, value=status)
            wb.save(wb_path)
            print(f"Saved to: {wb_path} (sheet '{SHEET_NAME}', row {row_idx})")
            return
    print(f"Warning: {test_case_id} not found in sheet '{SHEET_NAME}'.")


def run_configurable_test(
    test_case_id: str,
    route: str,
    test_fn: Callable[[ConfigurableSession], str],
    docstring: str | None = "",
) -> None:
    title = (docstring or test_case_id).strip().splitlines()[0]
    allure_writer = AllureStandaloneWriter(test_case_id, title, docstring or "")
    driver = _build_driver()
    wait = WebDriverWait(driver, 15)
    session = ConfigurableSession(driver, wait, allure_writer)

    try:
        actual = test_fn(session)
        shot = _save_evidence(driver, test_case_id, "PASS")
        allure_writer.attach_png(shot, "Pass Evidence")
        allure_writer.finalize("passed", actual)
        _update_excel(test_case_id, "Pass", actual)
        print(f"\n{test_case_id}: Pass - {actual}")
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {exc}"
        shot = _save_evidence(driver, test_case_id, "FAIL")
        allure_writer.attach_png(shot, "Failure Screenshot")
        allure_writer.finalize("failed", err_msg, traceback.format_exc())
        _update_excel(test_case_id, "Fail", err_msg)
        print(f"\n{test_case_id}: Fail - {err_msg}")
    finally:
        driver.quit()