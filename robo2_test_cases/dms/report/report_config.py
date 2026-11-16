"""Configuration for the Report test suite. Secrets are read from the root .env file."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


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
    if not username or not password:
        raise ReportConfigError(
            f"Missing credentials for profile '{profile_key}'. Set "
            f"{prefix}_USERNAME and {prefix}_PASSWORD in the root .env file."
        )
    return UserProfile(profile_key, username, password)


def required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ReportConfigError(f"Set {name} in the root .env file before running this test.")
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
