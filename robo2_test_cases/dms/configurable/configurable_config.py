"""Configuration & credential loader for the Configurable test suite."""
from __future__ import annotations

from pathlib import Path
import sys

CONFIGURABLE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIGURABLE_DIR.parent
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
    require_env as _require_env,
    resolve_dir,
    shared_admin_credentials,
    shared_general_credentials,
)

CONFIGURABLE_ENV_FILE = CONFIGURABLE_DIR / ".env.configurable"
ENV_FILE = SHARED_ENV_FILE

# Precedence: OS/GUI environment variables > optional configurable/.env.configurable > shared dms/.env
load_suite_env(CONFIGURABLE_ENV_FILE)


class ConfigurableConfigError(EnvConfigError):
    """Raised when required Configurable suite credentials or config are missing."""


# Shared environment & credential settings
BASE_URL: str = env_str("BASE_URL").rstrip("/")
ADMIN_USERNAME, ADMIN_PASSWORD = shared_admin_credentials(
    user_keys=("CONFIGURABLE_USERNAME",),
    pass_keys=("CONFIGURABLE_PASSWORD",),
)
GENERAL_USERNAME, GENERAL_PASSWORD = shared_general_credentials(
    user_keys=("CONFIGURABLE_GENERAL_USERNAME",),
    pass_keys=("CONFIGURABLE_GENERAL_PASSWORD",),
)

TESTER_NAME: str = env_str("TESTER_NAME")
SHEET_NAME: str = env_str("CONFIGURABLE_SHEET_NAME", default="Configurable")
EXCEL_PATH: str = env_str("EXCEL_PATH")
EVIDENCE_LINK: str = env_str("EVIDENCE_LINK")
EVIDENCE_HEADER: str = env_str("EVIDENCE_HEADER", default="remark").lower()
HEADER_ROW: int = 4

SCREENSHOT_DIR: Path = resolve_dir("SCREENSHOT_DIR", "screenshots", base_dir=PROJECT_ROOT, create=True)
DOWNLOAD_DIR: Path = resolve_dir("DOWNLOAD_DIR", "downloads", base_dir=PROJECT_ROOT, create=True)
ALLURE_RESULTS_DIR: Path = resolve_dir(
    "CONFIGURABLE_ALLURE_RESULTS_DIR",
    "allure-results",
    fallback_keys=("ALLURE_RESULTS_DIR",),
    base_dir=PROJECT_ROOT,
    create=True,
)


def base_url() -> str:
    if not BASE_URL:
        raise ConfigurableConfigError(f"Set BASE_URL in {ENV_FILE}, then run again.")
    return BASE_URL


def route(name: str, default: str) -> str:
    key = f"CONFIGURABLE_ROUTE_{name.strip().upper()}"
    return env_str(key, default=default)


def env_value(name: str, default: str = "") -> str:
    key = name.strip()
    prefixed = f"CONFIGURABLE_{key.upper()}" if not key.upper().startswith("CONFIGURABLE_") else key
    return env_str(prefixed, key, default=default)


def download_dir() -> Path:
    return DOWNLOAD_DIR


def evidence_dir() -> Path:
    return SCREENSHOT_DIR


def excel_path() -> Path:
    return Path(active_excel_and_sheet()[0])


def admin_credentials() -> tuple[str, str]:
    if not (ADMIN_USERNAME and ADMIN_PASSWORD):
        raise ConfigurableConfigError(
            f"Set ADMIN_USERNAME and ADMIN_PASSWORD (or CONFIGURABLE_USERNAME / CONFIGURABLE_PASSWORD) in {ENV_FILE}, then run again."
        )
    return ADMIN_USERNAME, ADMIN_PASSWORD


def general_credentials() -> tuple[str, str]:
    if not (GENERAL_USERNAME and GENERAL_PASSWORD):
        raise ConfigurableConfigError(
            f"Set GENERAL_USERNAME and GENERAL_PASSWORD (or CONFIGURABLE_GENERAL_USERNAME / CONFIGURABLE_GENERAL_PASSWORD) in {ENV_FILE}, then run again."
        )
    return GENERAL_USERNAME, GENERAL_PASSWORD


def get_profile(role_key: str = "admin") -> UserProfile:
    """Resolve credentials for a Configurable suite role from shared dms/.env."""
    key = (role_key or "admin").strip().lower()
    prefix = f"CONFIGURABLE_PROFILE_{key.upper()}"

    override_user = env_str(f"{prefix}_USERNAME")
    override_pass = env_secret(f"{prefix}_PASSWORD")

    if key in {"admin", "manager"}:
        username = override_user or ADMIN_USERNAME
        password = override_pass or ADMIN_PASSWORD
        hint = "ADMIN_USERNAME and ADMIN_PASSWORD"
    elif key in {"general", "user"}:
        username = override_user or GENERAL_USERNAME
        password = override_pass or GENERAL_PASSWORD
        hint = "GENERAL_USERNAME and GENERAL_PASSWORD"
    else:
        username = override_user
        password = override_pass
        hint = f"{prefix}_USERNAME and {prefix}_PASSWORD"

    if not username or not password:
        raise ConfigurableConfigError(
            f"Missing credentials for role '{role_key}'. Set {hint} in {ENV_FILE}."
        )
    return UserProfile(role=key, username=username, password=password)


def is_headless() -> bool:
    return env_bool("CONFIGURABLE_HEADLESS", "HEADLESS", default=False)


def require_env(name: str, hint: str = "") -> str:
    return _require_env(name, hint, env_file=ENV_FILE, error_cls=ConfigurableConfigError)


def active_excel_and_sheet() -> tuple[str, str]:
    """Read active EXCEL_PATH and sheet name, honoring GUI/OS overrides first."""
    try:
        return _active_excel_and_sheet(
            SHEET_NAME,
            "CONFIGURABLE_SHEET_NAME",
            fallback_excel=EXCEL_PATH,
            base_dir=PROJECT_ROOT,
        )
    except EnvConfigError as exc:
        raise ConfigurableConfigError(str(exc)) from exc
