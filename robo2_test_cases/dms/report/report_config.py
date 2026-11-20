"""Configuration & credential loader for the Report test suite."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
REPORT_ENV_FILE = REPORT_DIR / ".env.report"

# Precedence: OS/GUI environment variables > report/.env.report > dms/.env
load_dotenv(REPORT_ENV_FILE, override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Roles that default to the Manager/Admin account (REPORT_MANAGER_*)
MANAGER_ROLES = {
    "core_report_manager",
    "dms_report_manager",
    "wf_admin",
    "wf_manager",
    "wf_related_process_user",
}


class ReportConfigError(RuntimeError):
    """Raised when required account credentials are missing from .env.report."""


@dataclass(frozen=True)
class UserProfile:
    role: str
    username: str
    password: str


def general_username() -> str:
    return os.getenv("REPORT_USERNAME", "").strip()


def manager_username() -> str:
    return (
        os.getenv("REPORT_MANAGER_USERNAME")
        or os.getenv("DMS_USERNAME")
        or ""
    ).strip()


def get_profile(role_key: str) -> UserProfile:
    """Resolve credentials for a role using .env.report (or an optional per-role override)."""
    key = role_key.strip().lower()
    prefix = f"REPORT_PROFILE_{key.upper()}"

    if key in MANAGER_ROLES:
        username = (os.getenv(f"{prefix}_USERNAME") or manager_username()).strip()
        password = (
            os.getenv(f"{prefix}_PASSWORD")
            or os.getenv("REPORT_MANAGER_PASSWORD")
            or os.getenv("DMS_PASSWORD")
            or ""
        )
        hint = "REPORT_MANAGER_USERNAME and REPORT_MANAGER_PASSWORD"
    else:
        username = (os.getenv(f"{prefix}_USERNAME") or general_username()).strip()
        password = (
            os.getenv(f"{prefix}_PASSWORD")
            or os.getenv("REPORT_PASSWORD")
            or ""
        )
        hint = "REPORT_USERNAME and REPORT_PASSWORD"

    if not username or not password:
        raise ReportConfigError(
            f"Missing credentials for role '{role_key}'. Set {hint} in {REPORT_ENV_FILE}."
        )
    return UserProfile(role=key, username=username, password=password)


def is_headless() -> bool:
    return os.getenv("REPORT_HEADLESS", "false").strip().lower() in {"1", "true", "yes"}


def table_selector() -> str:
    return os.getenv("REPORT_TABLE_SELECTOR", "").strip()


def date_selectors() -> tuple[str, str]:
    return (
        os.getenv("REPORT_DATE_FROM_SELECTOR", "input[type='date']:first-of-type").strip(),
        os.getenv("REPORT_DATE_TO_SELECTOR", "input[type='date']:last-of-type").strip(),
    )
