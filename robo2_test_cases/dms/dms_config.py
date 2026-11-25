"""Configuration & environment loader for the Robo2mation DMS test suite."""
from __future__ import annotations

import os
from pathlib import Path

from env_config import (
    SHARED_ENV_FILE,
    SUITE_ROOT,
    EnvConfigError,
    active_excel_and_sheet as _active_excel_and_sheet,
    env_bool,
    env_str,
    load_suite_env,
    require_env as _require_env,
    resolve_dir,
    shared_admin_credentials,
    shared_general_credentials,
)

DMS_DIR = SUITE_ROOT
ENV_FILE = SHARED_ENV_FILE

# Load shared dms/.env without overriding OS or GUI-injected variables
load_suite_env()


class DmsConfigError(EnvConfigError):
    """Raised when required configuration or environment variables are missing."""


# Core credentials & runner settings
BASE_URL: str = env_str("BASE_URL").rstrip("/")
USERNAME, PASSWORD = shared_admin_credentials(
    user_keys=("DMS_USERNAME",),
    pass_keys=("DMS_PASSWORD",),
)
OTHER_USERNAME, OTHER_PASSWORD = shared_general_credentials(
    user_keys=("OTHER_USERNAME",),
    pass_keys=("OTHER_PASSWORD",),
)

TESTER_NAME: str = env_str("TESTER_NAME")
SHEET_NAME: str = env_str("DMS_SHEET_NAME", "SHEET_NAME", default="DMS")
EXCEL_PATH: str = env_str("EXCEL_PATH")
EVIDENCE_LINK: str = env_str("EVIDENCE_LINK")
EVIDENCE_HEADER: str = env_str("EVIDENCE_HEADER", default="remark").lower()
HEADER_ROW: int = 4

# Directories
SAMPLE_DIR: Path = resolve_dir("SAMPLE_DIR", "test_files", base_dir=DMS_DIR, create=False)
SCREENSHOT_DIR: Path = resolve_dir("SCREENSHOT_DIR", "screenshots", base_dir=DMS_DIR, create=True)
DOWNLOAD_DIR: Path = resolve_dir("DOWNLOAD_DIR", "downloads", base_dir=DMS_DIR, create=True)
ALLURE_RESULTS_DIR: Path = resolve_dir(
    "DMS_ALLURE_RESULTS_DIR",
    "allure-results",
    fallback_keys=("ALLURE_RESULTS_DIR",),
    base_dir=DMS_DIR,
    create=True,
)

# Application routes
EXPLORER_URL: str = f"{BASE_URL}/dms/document/explorer/"
ROOT_URL: str = f"{BASE_URL}/dms/document/root"
DELETED_ROOT_URL: str = f"{BASE_URL}/dms/document/deleted-root"
RESTORE_URL: str = f"{BASE_URL}/dms/restore/"
CHECKOUT_URL: str = f"{BASE_URL}/dms/document/checkout/"
BULK_URL: str = f"{BASE_URL}/dms/document/upload/bulk-upload/"
REVIEW_URL: str = f"{BASE_URL}/dms/document/pending-for-review/"
MASTER_TABLE_URL: str = f"{BASE_URL}/dms/document/settings/master-table-method/"
ATTACH_URL: str = f"{BASE_URL}/dms/document/upload/standard_upload/"
PENDING_URL: str = f"{BASE_URL}/dms/document/upload/standard_upload/filesave/pendingmetalist/"
REQUESTED_DOWNLOAD_URL: str = f"{BASE_URL}/requested_downloads/view/"

# Supported attachment extensions (DMS-TC002 / DMS-TC003)
EXTENSIONS: list[str] = [
    "pdf", "png", "jpg", "jpeg", "svg", "gif", "mp3", "mp4", "doc", "docx",
    "xls", "xlsx", "csv", "ppt", "pptx", "msg", "eml", "txt",
]

DOC_TYPE_SEARCH_TERMS: list[str] = (
    [os.getenv("DOC_TYPE", "").strip()]
    if (os.getenv("DOC_TYPE") or "").strip()
    else ["/LMG DocType/", "LMG DocType"]
)

# Optional parent category name for temporary AUTO_* categorization tests
# (empty by default so categorization tests target root as expected).
TEST_PARENT_CATEGORY: str = env_str("TEST_PARENT_CATEGORY")


def is_headless() -> bool:
    return env_bool("DMS_HEADLESS", "HEADLESS", default=False)


def require_env(name: str, hint: str = "") -> str:
    return _require_env(name, hint, env_file=ENV_FILE, error_cls=DmsConfigError)


def require_other_user() -> tuple[str, str]:
    if not (OTHER_USERNAME and OTHER_PASSWORD):
        raise DmsConfigError(
            f"Set OTHER_USERNAME and OTHER_PASSWORD (or GENERAL_USERNAME / GENERAL_PASSWORD) in {ENV_FILE}, then run again."
        )
    return OTHER_USERNAME, OTHER_PASSWORD


def active_excel_and_sheet() -> tuple[str, str]:
    """Read latest EXCEL_PATH and SHEET_NAME from os.environ (GUI overrides .env)."""
    try:
        return _active_excel_and_sheet(
            SHEET_NAME,
            "DMS_SHEET_NAME",
            fallback_excel=EXCEL_PATH,
            base_dir=DMS_DIR,
        )
    except EnvConfigError as exc:
        raise DmsConfigError(str(exc)) from exc
