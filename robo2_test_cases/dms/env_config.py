"""Shared environment, credential, and path loader for DMS, Report, and Configurable suites."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

SUITE_ROOT = Path(__file__).resolve().parent
SHARED_ENV_FILE = SUITE_ROOT / ".env"


class EnvConfigError(RuntimeError):
    """Raised when required configuration or environment variables are missing."""


@dataclass(frozen=True)
class UserProfile:
    """Resolved authentication profile for a suite role."""

    role: str
    username: str
    password: str


def load_suite_env(*extra_env_files: Path) -> None:
    """Load optional suite-local env overrides followed by the shared dms/.env.

    Precedence (highest to lowest):
    1. Existing OS / CI / GUI environment variables (override=False)
    2. Optional suite-local env files passed via *extra_env_files
    3. Shared dms/.env
    """
    for env_file in extra_env_files:
        if env_file and env_file.is_file():
            load_dotenv(env_file, override=False)
    if SHARED_ENV_FILE.is_file():
        load_dotenv(SHARED_ENV_FILE, override=False)


def env_str(*keys: str, default: str = "") -> str:
    """Return the first non-empty stripped environment value across ``keys``."""
    for key in keys:
        if not key:
            continue
        raw = os.getenv(key)
        if raw is not None and raw.strip():
            return raw.strip()
    return default


def env_secret(*keys: str, default: str = "") -> str:
    """Return the first non-empty raw environment value without stripping whitespace."""
    for key in keys:
        if not key:
            continue
        raw = os.getenv(key)
        if raw:
            return raw
    return default


def env_bool(*keys: str, default: bool = False) -> bool:
    """Return a boolean parsed from the first non-empty key across ``keys``."""
    raw = env_str(*keys)
    if not raw:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def resolve_dir(
    env_key: str,
    default_name: str,
    *,
    fallback_keys: tuple[str, ...] = (),
    base_dir: Path = SUITE_ROOT,
    create: bool = True,
) -> Path:
    """Resolve a directory from env keys relative to ``base_dir``."""
    raw = env_str(env_key, *fallback_keys, default=default_name)
    path = Path(raw)
    resolved = path if path.is_absolute() else (base_dir / path).resolve()
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_excel_path(raw_excel: str = "", *, base_dir: Path = SUITE_ROOT) -> Path:
    """Resolve the active Excel workbook path from an explicit value or EXCEL_PATH."""
    candidate_raw = (raw_excel or os.environ.get("EXCEL_PATH") or "").strip()
    if not candidate_raw:
        raise EnvConfigError(f"EXCEL_PATH is not set in {SHARED_ENV_FILE} or environment.")

    excel_path = Path(candidate_raw)
    if excel_path.is_absolute():
        return excel_path

    for root in (base_dir, base_dir.parent, base_dir.parent.parent):
        cand = (root / excel_path).resolve()
        if cand.exists():
            return cand
    return (base_dir / excel_path).resolve()


def active_excel_and_sheet(
    default_sheet: str,
    sheet_env_key: str = "",
    *,
    fallback_excel: str = "",
    base_dir: Path = SUITE_ROOT,
) -> tuple[str, str]:
    """Read active EXCEL_PATH and sheet name, honoring GUI/OS overrides first."""
    raw_excel = (os.environ.get("EXCEL_PATH") or fallback_excel or "").strip()
    excel_path = resolve_excel_path(raw_excel, base_dir=base_dir)
    sheet_keys = ("SHEET_NAME", sheet_env_key) if sheet_env_key else ("SHEET_NAME",)
    sheet_name = env_str(*sheet_keys, default=default_sheet)
    return str(excel_path), sheet_name


def require_env(
    name: str,
    hint: str = "",
    *,
    env_file: Path = SHARED_ENV_FILE,
    error_cls: type[RuntimeError] = EnvConfigError,
) -> str:
    """Require a non-empty environment variable or raise ``error_cls``."""
    value = env_str(name)
    if not value:
        detail = f" {hint}" if hint else ""
        raise error_cls(f"Set {name} in {env_file}{detail}, then run again.")
    return value


def shared_admin_credentials(
    *,
    user_keys: tuple[str, ...] = (),
    pass_keys: tuple[str, ...] = (),
) -> tuple[str, str]:
    """Resolve primary admin/manager credentials from suite keys or shared ADMIN_* / DMS_*."""
    username = env_str(*user_keys, "ADMIN_USERNAME", "DMS_USERNAME")
    password = env_secret(*pass_keys, "ADMIN_PASSWORD", "DMS_PASSWORD")
    return username, password


def shared_general_credentials(
    *,
    user_keys: tuple[str, ...] = (),
    pass_keys: tuple[str, ...] = (),
) -> tuple[str, str]:
    """Resolve general-user credentials from suite keys or shared GENERAL_*."""
    username = env_str(*user_keys, "GENERAL_USERNAME")
    password = env_secret(*pass_keys, "GENERAL_PASSWORD")
    return username, password
