"""Configuration for the Report test suite (JSON-free, minimal .env.report)."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re

from dotenv import load_dotenv

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
REPORT_ENV_FILE = REPORT_DIR / ".env.report"

# Load root .env first, then report/.env.report without overriding shell/GUI variables
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(REPORT_ENV_FILE, override=False)

MANAGER_ROLES = {
    "core_report_manager",
    "dms_report_manager",
    "wf_admin",
    "wf_manager",
    "wf_all_process",
}

# Fallback aliases so you don't have to repeat identical filter values in .env.report
FILTER_KEY_FALLBACKS: dict[str, tuple[str, ...]] = {
    "REPORT_FILTER_USER": ("REPORT_FILTER_USERS_NAME", "REPORT_USERNAME"),
    "REPORT_FILTER_USERS": ("REPORT_FILTER_USERS_NAME", "REPORT_USERNAME"),
    "REPORT_FILTER_ALL_USERS": ("REPORT_FILTER_USERS_NAME", "REPORT_USERNAME"),
    "REPORT_FILTER_UPLOADER": ("REPORT_FILTER_USERS_NAME", "DMS_USERNAME"),
    "REPORT_FILTER_INITIATOR_NAME": ("REPORT_FILTER_USERS_NAME", "REPORT_USERNAME"),
    "REPORT_FILTER_IP": ("REPORT_FILTER_IP_ADDRESS",),
    "REPORT_FILTER_SOURCE_IP": ("REPORT_FILTER_IP_ADDRESS",),
    "REPORT_FILTER_OPERATION": ("REPORT_FILTER_OPERATIONS",),
    "REPORT_FILTER_ALL_OPERATION": ("REPORT_FILTER_OPERATIONS",),
}


class ReportConfigError(RuntimeError):
    """Raised when a required Report test setting is not configured."""


@dataclass(frozen=True)
class UserProfile:
    key: str
    username: str
    password: str


def get_profile(profile_key: str) -> UserProfile:
    """Resolve credentials for a role key using the 2 main accounts or role-specific overrides."""
    key = profile_key.strip().lower()
    prefix = f"REPORT_PROFILE_{key.upper()}"

    if key in MANAGER_ROLES:
        username = (
            os.getenv(f"{prefix}_USERNAME")
            or os.getenv("REPORT_MANAGER_USERNAME")
            or os.getenv("DMS_USERNAME")
            or ""
        ).strip()
        password = (
            os.getenv(f"{prefix}_PASSWORD")
            or os.getenv("REPORT_MANAGER_PASSWORD")
            or os.getenv("DMS_PASSWORD")
            or ""
        )
        hint = "REPORT_MANAGER_USERNAME and REPORT_MANAGER_PASSWORD"
    else:
        username = (
            os.getenv(f"{prefix}_USERNAME")
            or os.getenv("REPORT_USERNAME")
            or ""
        ).strip()
        password = (
            os.getenv(f"{prefix}_PASSWORD")
            or os.getenv("REPORT_PASSWORD")
            or ""
        )
        hint = "REPORT_USERNAME and REPORT_PASSWORD"

    if not username or not password:
        raise ReportConfigError(
            f"Missing credentials for profile '{profile_key}'. Set {hint} in {REPORT_ENV_FILE}."
        )
    return UserProfile(profile_key, username, password)


def required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ReportConfigError(f"Set {name} in {REPORT_ENV_FILE} before running this test.")
    return value


def _env_key_for_filter(label: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", label.strip()).strip("_").upper()
    return f"REPORT_FILTER_{slug}"


def filter_values(labels: list[str] | None = None) -> dict[str, str]:
    """Read filter values from plain REPORT_FILTER_<LABEL> keys in .env.report."""
    if not labels:
        return {}
    resolved: dict[str, str] = {}
    for label in labels:
        env_key = _env_key_for_filter(label)
        value = os.getenv(env_key, "").strip()
        if not value:
            for fallback_key in FILTER_KEY_FALLBACKS.get(env_key, ()):
                value = os.getenv(fallback_key, "").strip()
                if value:
                    break
        if not value:
            raise ReportConfigError(
                f"Missing test value for filter '{label}'. Set {env_key} in {REPORT_ENV_FILE}."
            )
        resolved[label] = value
    return resolved


def table_selector() -> str:
    return os.getenv("REPORT_TABLE_SELECTOR", "").strip()


def date_selectors() -> tuple[str, str]:
    return (
        os.getenv("REPORT_DATE_FROM_SELECTOR", "input[type='date']:first-of-type").strip(),
        os.getenv("REPORT_DATE_TO_SELECTOR", "input[type='date']:last-of-type").strip(),
    )


def expected_value(name: str) -> str:
    return os.getenv(name, "").strip()