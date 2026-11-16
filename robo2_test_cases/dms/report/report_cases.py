"""The 102 Report-sheet cases and their execution behaviour."""
from __future__ import annotations

import json
import os
from pathlib import Path

_DATA_FILE = Path(__file__).with_name("report_cases_source.json")
with _DATA_FILE.open(encoding="utf-8") as source:
    _SOURCE = {item["test_case_id"]: item for item in json.load(source)}


def _group(number: int):
    groups = [
        (1, 5, "core_login"), (6, 12, "core_activity"), (13, 17, "core_api"),
        (18, 23, "dms_activity"), (24, 24, "document_summary"),
        (25, 30, "upload_record"), (31, 36, "document_record"),
        (37, 42, "archived_document_record"), (43, 48, "document_type"),
        (49, 54, "page_count"), (55, 63, "kpi"), (64, 71, "task_activity"),
        (72, 78, "application_activity"), (79, 86, "workflow_activity"),
        (87, 94, "custom_report"), (95, 102, "auto_approval"),
    ]
    return next(name for start, end, name in groups if start <= number <= end)


def _profile_for(group: str, offset: int) -> tuple[str, str]:
    """Returns (profile key, expected visibility mode) for the row's documented scenario."""
    if group == "core_login":
        return ("core_user", "own") if offset == 1 else ("core_report_manager", "all")
    if group == "core_activity":
        if offset == 1 or offset == 3:
            return "core_user", "own" if offset == 1 else "accessible"
        return "core_report_manager", "all" if offset == 2 else "accessible"
    if group == "core_api":
        return ("core_user", "denied") if offset == 1 else ("core_report_manager", "all" if offset == 2 else "accessible")
    if group == "dms_activity":
        return ("dms_user", "own") if offset == 1 else ("dms_report_manager", "all" if offset == 2 else "accessible")
    if group == "document_summary":
        return "dms_report_manager", "multi"
    if group == "upload_record":
        # Both role scenarios in the supplied worksheet expect the user's own uploads.
        return ("dms_user", "own") if offset == 1 else ("dms_report_manager", "own" if offset == 2 else "accessible")
    if group in {"document_record", "archived_document_record"}:
        # The non-manager scenario is limited to document types where the user is
        # assigned through access/owner/LMG group membership (not simply own uploads).
        return ("dms_assigned_user", "related") if offset == 1 else ("dms_report_manager", "all" if offset == 2 else "accessible")
    if group in {"document_type", "page_count"}:
        return ("dms_user", "own") if offset == 1 else ("dms_report_manager", "all" if offset == 2 else "accessible")
    if group == "kpi":
        return {
            1: ("wf_unassigned_user", "own"), 2: ("wf_admin", "all"),
            3: ("wf_manager", "department"), 4: ("wf_general_user", "own"),
        }.get(offset, ("wf_admin", "accessible"))
    workflow_roles = {
        "task_activity": {1: ("wf_no_process_info", "own"), 2: ("wf_related_process", "related"), 3: ("wf_all_process", "all")},
        "application_activity": {1: ("wf_no_process_info", "own"), 2: ("wf_related_process", "related"), 3: ("wf_all_process", "all")},
        "workflow_activity": {1: ("wf_no_process_info", "own"), 2: ("wf_related_process", "related"), 3: ("wf_all_process", "all")},
        "custom_report": {1: ("wf_no_process_info", "own"), 2: ("wf_related_process", "related"), 3: ("wf_all_process", "all")},
        "auto_approval": {1: ("wf_no_process_info", "own"), 2: ("wf_related_process", "related"), 3: ("wf_all_process", "all")},
    }
    mapping = workflow_roles.get(group, {})
    return mapping.get(offset, ("wf_all_process", "accessible"))


def _details(number: int, group: str, offset: int) -> dict:
    action = "open"
    labels: list[str] = []
    sort_labels: list[str] = []
    export_actions: list[str] = []
    page_size = ""
    download_mode = ""

    if group == "core_login":
        action = {1: "scope", 2: "scope", 3: "search", 4: "date", 5: "export"}[offset]
        labels = ["Users Name", "IP Address"] if offset == 3 else []
        export_actions = ["Copy", "CSV", "Print"] if offset == 5 else []
    elif group == "core_activity":
        action = {1: "scope", 2: "scope", 3: "open", 4: "search", 5: "date", 6: "sort", 7: "export"}[offset]
        labels = ["Users Name", "Operations"] if offset == 4 else []
        sort_labels = ["Users Name", "Operation", "Description", "IP Address"] if offset == 6 else []
        export_actions = ["Copy", "CSV", "Print"] if offset == 7 else []
    elif group == "core_api":
        action = {1: "deny", 2: "scope", 3: "search", 4: "date", 5: "export"}[offset]
        labels = ["REQUEST URL", "IP", "METHOD", "STATUS CODE"] if offset == 3 else []
        export_actions = ["Copy", "CSV", "Print"] if offset == 5 else []
        page_size = "10,20,50,all" if offset == 5 else ""
    elif group == "dms_activity":
        action = {1: "scope", 2: "scope", 3: "search", 4: "date", 5: "filter", 6: "export"}[offset]
        labels = (["User", "Operation", "Source IP"] if offset == 3 else ["All Operation", "All Users"] if offset == 5 else [])
        export_actions = ["Copy", "CSV", "Excel", "Print"] if offset == 6 else []
        download_mode = "requested" if offset == 6 else ""
    elif group == "document_summary":
        action = "multi_scope"
    elif group in {"upload_record", "document_record", "archived_document_record"}:
        action = {1: "scope", 2: "scope", 3: "search", 4: "date", 5: "filter", 6: "export"}[offset]
        labels = (["Uploader", "Document Name", "Document Type", "Metafield"] if offset == 3 else ["Document Type"] if offset == 5 else [])
        export_actions = ["Excel"] if offset == 6 else []
        download_mode = "requested" if offset == 6 else ""
    elif group == "document_type":
        action = {1: "scope", 2: "scope", 3: "search", 4: "date", 5: "filter", 6: "export"}[offset]
        labels = (["Document Type", "Access Group", "Owner Group", "Full Path"] if offset == 3 else ["Users"] if offset == 5 else [])
        export_actions = ["Excel"] if offset == 6 else []
        download_mode = "requested" if offset == 6 else ""
    elif group == "page_count":
        action = {1: "scope", 2: "scope", 3: "search", 4: "date", 5: "filter", 6: "export"}[offset]
        labels = ["Document Type"]
        export_actions = ["Copy", "CSV", "Print"] if offset == 6 else []
    elif group == "kpi":
        action = {1: "scope", 2: "scope", 3: "scope", 4: "scope", 5: "search", 6: "filter", 7: "date", 8: "download_direct", 9: "download_requested"}[offset]
        labels = (["User"] if offset == 5 else ["User", "Department"] if offset == 6 else [])
        download_mode = "direct" if offset == 8 else "requested" if offset == 9 else ""
        export_actions = ["Excel", "CSV"] if offset in (8, 9) else []
    elif group in {"task_activity", "application_activity", "workflow_activity", "custom_report", "auto_approval"}:
        # Each workflow report's first three rows are role/permission visibility cases.
        if offset in (1, 2, 3):
            action = "scope"
        else:
            operation_index = offset - 3
            if group == "task_activity":
                operation_map = {1: "search", 2: "date", 3: "filter", 4: "download_requested", 5: "download_direct"}
            elif group == "application_activity":
                operation_map = {1: "search", 2: "date", 3: "download_requested", 4: "download_direct"}
            elif group == "workflow_activity":
                operation_map = {1: "search", 2: "filter", 3: "date", 4: "download_requested", 5: "download_direct"}
            elif group == "custom_report":
                operation_map = {1: "search", 2: "date", 3: "filter", 4: "download_requested", 5: "download_direct"}
            else:
                operation_map = {1: "search", 2: "sort", 3: "date", 4: "filter", 5: "export"}
            action = operation_map.get(operation_index, "open")
        labels = {
            "task_activity": ["Project", "App Number", "User", "Status"],
            "application_activity": ["Project", "App Number", "User", "Status"],
            "workflow_activity": ["Project", "App Number", "User", "Status"],
            "custom_report": ["Project", "App Number", "User", "Status"],
            "auto_approval": ["Project", "App Number", "User", "Status"],
        }.get(group, []) if action == "search" else []
        if group == "task_activity" and action == "filter": labels = ["User"]
        if group == "workflow_activity" and action == "filter": labels = ["Process"]
        if group == "custom_report" and action == "filter": labels = ["Status", "Initiator Name"]
        if group == "auto_approval" and action == "filter": labels = ["Process", "Status"]
        if action == "sort":
            sort_labels = ["Any"] if group == "auto_approval" else ["Users Name", "Operation", "Description", "IP Address"]
        if action in ("download_direct", "download_requested"):
            download_mode = "direct" if action == "download_direct" else "requested"
            export_actions = [os.getenv("REPORT_DIRECT_EXPORT_ACTION", "CSV")] if action == "download_direct" else ["Download"]
        if action == "export":
            export_actions = ["CSV", "Excel"]
    if action == "export" and not export_actions:
        export_actions = ["CSV"]
    if action == "download_direct" and not export_actions:
        export_actions = ["CSV"]

    profile, visibility = _profile_for(group, offset)
    profiles = [(profile, visibility)]
    if group == "document_summary":
        profiles = [("dms_report_manager", "all"), ("dms_user", "own")]
    return {
        "action": action,
        "profiles": profiles,
        "visibility": visibility,
        "filter_labels": labels,
        "sort_labels": sort_labels,
        "export_actions": export_actions,
        "page_size": page_size,
        "download_mode": download_mode,
    }


def get_case(test_case_id: str) -> dict:
    source = _SOURCE.get(test_case_id)
    if source is None:
        raise KeyError(f"Unknown Report test case ID: {test_case_id}")
    number = int(test_case_id.rsplit("TC", 1)[1])
    group = _group(number)
    offset = number - {
        "core_login": 0, "core_activity": 5, "core_api": 12, "dms_activity": 17,
        "document_summary": 23, "upload_record": 24, "document_record": 30,
        "archived_document_record": 36, "document_type": 42, "page_count": 48,
        "kpi": 54, "task_activity": 63, "application_activity": 71,
        "workflow_activity": 78, "custom_report": 86, "auto_approval": 94,
    }[group]
    return {**source, "feature": source["functional_area"], **_details(number, group, offset)}


def all_cases() -> list[dict]:
    return [get_case(test_id) for test_id in sorted(_SOURCE, key=lambda value: int(value.rsplit("TC", 1)[1]))]
