"""Configuration & credential loader for the Report test suite."""
from __future__ import annotations

import os
from pathlib import Path
import sys

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env_config import (  # noqa: E402
    SHARED_ENV_FILE,
    EnvConfigError,
    UserProfile,
    active_excel_and_sheet as _active_excel_and_sheet,
    env_bool,
    env_secret,
    env_str,
    load_suite_env,
    resolve_dir,
    shared_admin_credentials,
    shared_general_credentials,
)

REPORT_ENV_FILE = REPORT_DIR / ".env.report"
ENV_FILE = SHARED_ENV_FILE

# Precedence: OS/GUI environment variables > optional report/.env.report > shared dms/.env
load_suite_env(REPORT_ENV_FILE)

# Roles that default to the Manager/Admin account (ADMIN_* / REPORT_MANAGER_*)
MANAGER_ROLES = {
    "core_report_manager",
    "dms_report_manager",
    "wf_admin",
    "wf_manager",
    "wf_related_process_user",
}


class ReportConfigError(EnvConfigError):
    """Raised when required account credentials or configuration are missing."""


# Shared environment settings
BASE_URL: str = env_str("BASE_URL").rstrip("/")
TESTER_NAME: str = env_str("TESTER_NAME")
SHEET_NAME: str = env_str("REPORT_SHEET_NAME", default="Report")
EXCEL_PATH: str = env_str("EXCEL_PATH")
EVIDENCE_LINK: str = env_str("EVIDENCE_LINK")
EVIDENCE_HEADER: str = env_str("EVIDENCE_HEADER", default="remark").lower()
HEADER_ROW: int = 4

SCREENSHOT_DIR: Path = resolve_dir("SCREENSHOT_DIR", "screenshots", base_dir=PROJECT_ROOT, create=True)
DOWNLOAD_DIR: Path = resolve_dir("DOWNLOAD_DIR", "downloads", base_dir=PROJECT_ROOT, create=True)
ALLURE_RESULTS_DIR: Path = resolve_dir(
    "REPORT_ALLURE_RESULTS_DIR",
    "allure-results",
    fallback_keys=("ALLURE_RESULTS_DIR",),
    base_dir=PROJECT_ROOT,
    create=True,
)
REQUESTED_DOWNLOAD_URL: str = f"{BASE_URL}/requested_downloads/view/"


def general_username() -> str:
    return env_str("REPORT_USERNAME", "GENERAL_USERNAME")


def general_password() -> str:
    return env_secret("REPORT_PASSWORD", "GENERAL_PASSWORD")


def manager_username() -> str:
    return shared_admin_credentials(
        user_keys=("REPORT_MANAGER_USERNAME",),
        pass_keys=("REPORT_MANAGER_PASSWORD",),
    )[0]


def manager_password() -> str:
    return shared_admin_credentials(
        user_keys=("REPORT_MANAGER_USERNAME",),
        pass_keys=("REPORT_MANAGER_PASSWORD",),
    )[1]


def get_profile(role_key: str) -> UserProfile:
    """Resolve credentials for a role from shared dms/.env (or optional overrides)."""
    key = role_key.strip().lower()
    prefix = f"REPORT_PROFILE_{key.upper()}"

    if key in MANAGER_ROLES:
        username = env_str(f"{prefix}_USERNAME") or manager_username()
        password = env_secret(f"{prefix}_PASSWORD") or manager_password()
        hint = (
            "ADMIN_USERNAME and ADMIN_PASSWORD "
            "(or REPORT_MANAGER_USERNAME / REPORT_MANAGER_PASSWORD)"
        )
    else:
        username = env_str(f"{prefix}_USERNAME") or general_username()
        password = env_secret(f"{prefix}_PASSWORD") or general_password()
        hint = (
            "GENERAL_USERNAME and GENERAL_PASSWORD "
            "(or REPORT_USERNAME / REPORT_PASSWORD)"
        )

    if not username or not password:
        raise ReportConfigError(
            f"Missing credentials for role '{role_key}'. Set {hint} in {ENV_FILE}."
        )
    return UserProfile(role=key, username=username, password=password)


def is_headless() -> bool:
    return env_bool("REPORT_HEADLESS", "HEADLESS", default=False)


def active_excel_and_sheet() -> tuple[str, str]:
    """Read active EXCEL_PATH and sheet name, honoring GUI/OS overrides first."""
    try:
        return _active_excel_and_sheet(
            SHEET_NAME,
            "REPORT_SHEET_NAME",
            fallback_excel=EXCEL_PATH,
            base_dir=PROJECT_ROOT,
        )
    except EnvConfigError as exc:
        raise ReportConfigError(str(exc)) from exc


def table_selector() -> str:
    return os.getenv("REPORT_TABLE_SELECTOR", "").strip()


def date_selectors() -> tuple[str, str]:
    return (
        os.getenv("REPORT_DATE_FROM_SELECTOR", "input[type='date']:first-of-type").strip(),
        os.getenv("REPORT_DATE_TO_SELECTOR", "input[type='date']:last-of-type").strip(),
    )
