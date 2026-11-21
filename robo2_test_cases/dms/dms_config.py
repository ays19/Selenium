"""Configuration & environment loader for the Robo2mation DMS test suite."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DMS_DIR = Path(__file__).resolve().parent
ENV_FILE = DMS_DIR / ".env"

# Load dms/.env without overriding OS or GUI-injected variables (EXCEL_PATH, SHEET_NAME)
load_dotenv(ENV_FILE, override=False)


class DmsConfigError(RuntimeError):
    """Raised when required configuration or environment variables are missing."""


def _resolve_dir(env_key: str, default_name: str, create: bool = True) -> Path:
    raw = (os.getenv(env_key) or default_name).strip()
    path = Path(raw)
    resolved = path if path.is_absolute() else (DMS_DIR / path).resolve()
    if create:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


# Core credentials & runner settings
BASE_URL: str = (os.getenv("BASE_URL") or "").strip().rstrip("/")
USERNAME: str = (os.getenv("DMS_USERNAME") or "").strip()
PASSWORD: str = os.getenv("DMS_PASSWORD") or ""
OTHER_USERNAME: str = (os.getenv("OTHER_USERNAME") or "").strip()
OTHER_PASSWORD: str = os.getenv("OTHER_PASSWORD") or ""

TESTER_NAME: str = (os.getenv("TESTER_NAME") or "").strip()
SHEET_NAME: str = (os.getenv("SHEET_NAME") or "DMS").strip()
EXCEL_PATH: str = (os.getenv("EXCEL_PATH") or "").strip()
EVIDENCE_LINK: str = (os.getenv("EVIDENCE_LINK") or "").strip()
EVIDENCE_HEADER: str = (os.getenv("EVIDENCE_HEADER") or "remark").strip().lower()
HEADER_ROW: int = 4

# Directories
SAMPLE_DIR: Path = _resolve_dir("SAMPLE_DIR", "test_files", create=False)
SCREENSHOT_DIR: Path = _resolve_dir("SCREENSHOT_DIR", "screenshots", create=True)
DOWNLOAD_DIR: Path = _resolve_dir("DOWNLOAD_DIR", "downloads", create=True)
ALLURE_RESULTS_DIR: Path = _resolve_dir("DMS_ALLURE_RESULTS_DIR", "allure-results", create=True)

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
    else ["1 FC Test updated/aa", "aa", "doc", "inv", "rep", "con", "ent", "ion", "ing"]
)

# Optional parent category name for temporary AUTO_* categorization tests
# (empty by default so categorization tests target root as expected).
TEST_PARENT_CATEGORY: str = (os.getenv("TEST_PARENT_CATEGORY") or "").strip()


def is_headless() -> bool:
    return (os.getenv("DMS_HEADLESS") or "false").strip().lower() in {"1", "true", "yes"}


def require_env(name: str, hint: str = "") -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        detail = f" {hint}" if hint else ""
        raise DmsConfigError(f"Set {name} in {ENV_FILE}{detail}, then run again.")
    return value


def require_other_user() -> tuple[str, str]:
    if not (OTHER_USERNAME and OTHER_PASSWORD):
        raise DmsConfigError(
            f"Set OTHER_USERNAME and OTHER_PASSWORD in {ENV_FILE} (a second permitted general user), then run again."
        )
    return OTHER_USERNAME, OTHER_PASSWORD


def active_excel_and_sheet() -> tuple[str, str]:
    """Read latest EXCEL_PATH and SHEET_NAME from os.environ (GUI overrides .env)."""
    raw_excel = (os.environ.get("EXCEL_PATH") or EXCEL_PATH or "").strip()
    if not raw_excel:
        raise DmsConfigError(f"EXCEL_PATH is not set in {ENV_FILE} or environment.")
    excel_path = Path(raw_excel)
    if not excel_path.is_absolute():
        candidate = (DMS_DIR / excel_path).resolve()
        if candidate.exists():
            excel_path = candidate
        else:
            repo_cand = (DMS_DIR.parent.parent / excel_path).resolve()
            excel_path = repo_cand if repo_cand.exists() else candidate
    sheet_name = (os.environ.get("SHEET_NAME") or SHEET_NAME or "DMS").strip()
    return str(excel_path), sheet_name
