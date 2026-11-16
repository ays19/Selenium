"""Configuration for the Report test suite.

Settings are read from report/.env.report (role credentials, expected values) with the
root dms/.env and shell environment taking priority when the same key is set there.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Optional report-only settings (role profile credentials etc.) kept next to this file so
# the root .env never needs to change. override=False: values already in the environment
# (shell / GUI / root .env) always win over this file.
REPORT_ENV_FILE = Path(__file__).resolve().parent / ".env.report"
load_dotenv(REPORT_ENV_FILE, override=False)


class ReportConfigError(RuntimeError):
    """Raised when a required Report test setting is not configured."""


@dataclass(frozen=True)
class UserProfile:
    key: str
    username: str
    password: str


def get_profile(profile_key: str) -> UserProfile:
    prefix = f"REPORT_PROFILE_{profile_key.upper()}"
    username = os.getenv(f"{prefix}_USERNAME", "").strip()
    password = os.getenv(f"{prefix}_PASSWORD", "")
    # Generic report account in .env.report is the regular core user.
    if profile_key == "core_user" and (not username or not password):
        username = os.getenv("REPORT_USERNAME", "").strip()
        password = os.getenv("REPORT_PASSWORD", "")
    if not username or not password:
        hint = "REPORT_USERNAME and REPORT_PASSWORD" if profile_key == "core_user" else (
            f"{prefix}_USERNAME and {prefix}_PASSWORD"
        )
        raise ReportConfigError(
            f"Missing credentials for profile '{profile_key}'. Set {hint} in {REPORT_ENV_FILE}."
        )
    return UserProfile(profile_key, username, password)


def required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ReportConfigError(f"Set {name} in {REPORT_ENV_FILE} before running this test.")
    return value


def filter_values() -> dict[str, str]:
    raw = os.getenv("REPORT_FILTER_VALUES_JSON", "{}").strip() or "{}"
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReportConfigError(f"REPORT_FILTER_VALUES_JSON is invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReportConfigError("REPORT_FILTER_VALUES_JSON must be a JSON object of field labels and values.")
    return {str(key): str(value) for key, value in data.items()}


def expected_value(name: str) -> str:
    return os.getenv(name, "").strip()
