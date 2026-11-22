"""
Data-driven test data for the Robo2mation Report test suite.

Separation of concerns:
- .env.report    -> secrets & account credentials ONLY
- report_data.py -> search inputs, filter values, expected texts, and date ranges
"""
from __future__ import annotations

from datetime import date, timedelta

from report.report_config import general_username, manager_username

# Usernames read once from .env.report (never duplicated in config)
GENERAL_USER = general_username()
MANAGER_USER = manager_username()

# Default document type used by DMS document reports
DEFAULT_DOC_TYPE = "aa"

# Optional expected text for Core API Report access check (REP-TC014)
EXPECTED_API_TEXT = ""

# Optional expected text on Requested Downloads page
EXPECTED_DOWNLOAD_TEXT = ""

# Rolling date range window (days back from today) for date-filter tests
DEFAULT_DATE_RANGE_DAYS = 30

# Expected "other user" text when verifying "all" scope per role.
# Roles not listed here default to GENERAL_USER (proving manager sees another user's rows).
ROLE_EXPECTED_ALL_TEXT: dict[str, str] = {
    "core_report_manager": GENERAL_USER,
    "dms_report_manager": GENERAL_USER,
    "wf_related_process_user": MANAGER_USER,
    "wf_admin": "admin",
    "wf_manager": "admin",
}

# Shared default values by field label (used when a report has no specific override)
DEFAULT_FILTER_VALUES: dict[str, str] = {
    "Users Name": MANAGER_USER,
    "User": MANAGER_USER,
    "Users": MANAGER_USER,
    "All Users": MANAGER_USER,
    "Uploader": MANAGER_USER,
    "Initiator Name": MANAGER_USER,
    "IP Address": "192.168.51.201",
    "IP": "192.168.51.201",
    "Source IP": "192.168.51.201",
    "Operations": "Login",
    "Operation": "Login",
    "Document Type": DEFAULT_DOC_TYPE,
}

# Per-report search & filter test datasets
REPORT_FILTERS: dict[str, dict] = {
    "core_login": {
        "filters": {"Users Name": MANAGER_USER, "IP Address": "192.168.51.201"},
        "expected": MANAGER_USER,
    },
    "core_activity": {
        "filters": {"Users Name": MANAGER_USER, "Operations": "Login"},
        "expected": MANAGER_USER,
    },
    "core_api": {
        "filters": {
            "REQUEST URL": "/api/",
            "IP": "192.168.51.201",
            "METHOD": "GET",
            "STATUS CODE": "200",
        },
        "expected": "200",
    },
    "dms_activity_search": {
        "filters": {
            "User": MANAGER_USER,
            "Operation": "Login",
            "Source IP": "192.168.51.201",
        },
        "expected": "Attach Document",
    },
    "dms_activity_filter": {
        "filters": {
            "All Operation": "Attach Document",
            "All Users": MANAGER_USER,
        },
        "expected": "Attach Document",
    },
    "upload_record": {
        # Dynamic fields (Document Name, Metafield) are read from the loaded table row.
        "filters": {"Uploader": MANAGER_USER, "Document Type": DEFAULT_DOC_TYPE},
        "expected": "",
    },
    "document_record": {
        # Dynamic fields (Document Name, Metafield) are read from the loaded table row.
        "filters": {"Uploader": MANAGER_USER, "Document Type": DEFAULT_DOC_TYPE},
        "expected": "",
    },
    "archived_document_record": {
        "filters": {
            "Uploader": MANAGER_USER,
            "Document Name": "AUTO_143605",
            "Document Type": DEFAULT_DOC_TYPE,
            "Metafield": "97025187",
        },
        "expected": MANAGER_USER,
    },
    "document_type": {
        "filters": {
            "Document Type": DEFAULT_DOC_TYPE,
            "Access Group": "Avengers1",
            "Owner Group": "Avengers1",
            "Full Path": "/Without Checker/Bulk Up/",
        },
        "expected": "Bulk Up",
    },
    "page_count": {
        "filters": {"Document Type": DEFAULT_DOC_TYPE},
        "expected": DEFAULT_DOC_TYPE,
    },
    "kpi_search": {
        "filters": {"User": MANAGER_USER},
        "expected": MANAGER_USER,
    },
    "kpi_filter": {
        "filters": {"User": MANAGER_USER, "Department": "122"},
        "expected": MANAGER_USER,
    },
    "task_activity": {
        # Dynamic fields (Project, App Number, Status) are read from the loaded table row.
        "filters": {"User": MANAGER_USER},
        "expected": "",
    },
    "application_activity": {
        # Dynamic fields (Project, App Number, Status) are read from the loaded table row.
        "filters": {"User": MANAGER_USER},
        "expected": "",
    },
    "workflow_activity": {
        "filters": {
            "User": GENERAL_USER,
            "Operation": "Create Process Category",
            "Source IP": "192.168.51.201",
        },
        "expected": "",
    },
    "custom_report": {
        # Dynamic fields (App Number, User, Status) are read from the loaded table row.
        "filters": {"User": ""},
        "expected": "",
    },
    "custom_report_filter": {
        "filters": {
            "Status": "Pending",
            "Initiator Name": MANAGER_USER,
        },
        "expected": "Pending",
    },
}


def get_date_range(days_back: int = DEFAULT_DATE_RANGE_DAYS) -> tuple[str, str]:
    """Return a rolling (date_from, date_to) pair in DD-MM-YYYY format."""
    today = date.today()
    start = today - timedelta(days=days_back)
    return start.strftime("%d-%m-%Y"), today.strftime("%d-%m-%Y")


def expected_scope_texts(role_key: str) -> tuple[str, str]:
    """Return (own_text, other_text) for verifying role-based data visibility."""
    role = role_key.strip().lower()
    own_text = GENERAL_USER
    other_text = ROLE_EXPECTED_ALL_TEXT.get(role, MANAGER_USER)
    return own_text, other_text


def get_filter_data(report_key: str, labels: list[str]) -> tuple[dict[str, str], str]:
    """Return (configured_filters_dict, expected_result_text) for a report."""
    entry = REPORT_FILTERS.get(report_key, {})
    specific = entry.get("filters", {})

    resolved: dict[str, str] = {}
    for label in labels:
        raw = specific[label] if label in specific else DEFAULT_FILTER_VALUES.get(label)
        value = (raw or "").strip()
        if value:
            resolved[label] = value

    expected = (entry.get("expected") or "").strip()
    return resolved, expected
