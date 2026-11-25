"""
Robo2mation Test Automation Suite Desktop Client
Supports Module Selection (ALL, DMS, Core, Workflow, Reports),
High-DPI crystal-clear display, Live Execution Charts, and standalone PyInstaller compilation.
"""

from datetime import datetime
import importlib
import inspect
import math
import os
from pathlib import Path
import queue
import runpy
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


# ENABLE WINDOWS HIGH-DPI AWARENESS (Fixes Blurriness)
try:
    import ctypes

    # 2 = Per-Monitor DPI Aware (Windows 10/11)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Determine root folder whether running in source code or PyInstaller frozen bundle
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = APP_DIR

# Ensure APP_DIR is searched FIRST so updated common.py / tc*.py files override _internal
for p in [str(BUNDLE_DIR), str(APP_DIR)]:
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

# Load .env from APP_DIR (if present) without overriding existing environment variables
try:
    from dotenv import load_dotenv as _load_dotenv

    if (APP_DIR / ".env").exists():
        _load_dotenv(APP_DIR / ".env", override=False)
except Exception:
    pass


def find_script_path(script_name: str) -> Path | None:
    """Finds a test script (including subfolder paths like 'core/user_management.py')
    whether alongside the exe or inside _internal."""
    for base in [APP_DIR, BUNDLE_DIR]:
        candidate = base / script_name
        if candidate.exists():
            return candidate
    return None


def _resolve_default_excel() -> str:
    """Prefer EXCEL_PATH from .env when it exists; fall back to a local copy next to the app."""
    local_excel = APP_DIR / "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"
    env_raw = os.getenv("EXCEL_PATH", "").strip()
    if env_raw:
        env_path = Path(env_raw)
        if not env_path.is_absolute():
            for base in (APP_DIR, APP_DIR.parent, APP_DIR.parent.parent):
                cand = (base / env_path).resolve()
                if cand.is_file():
                    return str(cand)
        elif env_path.is_file():
            return str(env_path.resolve())
    if local_excel.is_file():
        return str(local_excel)
    parent_excel = APP_DIR.parent / "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"
    if parent_excel.is_file():
        return str(parent_excel)
    return env_raw or str(local_excel)


# SUBPROCESS WORKER DISPATCHER

def run_as_worker():
    """Runs a single test case file in process isolation when called with CLI args."""
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker-test":
        test_module_name = sys.argv[2]
        sheet_name = sys.argv[3] if len(sys.argv) > 3 else "DMS"
        gui_excel_path = os.environ.get("EXCEL_PATH")
        os.environ["SHEET_NAME"] = sheet_name

        try:
            script_path = find_script_path(test_module_name)
            if not script_path or not script_path.exists():
                print(f"[!] FAIL: Could not locate script: {test_module_name}")
                sys.exit(1)

            script_dir = str(script_path.parent)
            rel_parent = Path(test_module_name).parent

            # Ensure subfolder paths (e.g. report/, core/) precede root APP_DIR so
            # local imports like `import common as c` resolve to the module's own common.py.
            priority_dirs = []
            for base in (BUNDLE_DIR, APP_DIR):
                sub_dir = base / rel_parent
                if sub_dir.exists():
                    priority_dirs.append(str(sub_dir))
            priority_dirs.append(script_dir)

            for dir_path in priority_dirs:
                while dir_path in sys.path:
                    sys.path.remove(dir_path)
                sys.path.insert(0, dir_path)

            os.chdir(script_dir)

            # Load suite-local override files and shared .env without overwriting GUI's EXCEL_PATH/SHEET_NAME
            env_candidates = []
            for base_dir in dict.fromkeys([APP_DIR / rel_parent, Path(script_dir)]):
                for env_name in (".env.report", ".env.configurable", ".env"):
                    env_file = base_dir / env_name
                    if env_file.is_file():
                        env_candidates.append(env_file)

            if env_candidates:
                try:
                    from dotenv import load_dotenv

                    for env_file in env_candidates:
                        load_dotenv(env_file, override=False)
                except Exception:
                    pass

            if gui_excel_path:
                os.environ["EXCEL_PATH"] = gui_excel_path
            os.environ["SHEET_NAME"] = sheet_name

            # Check whether the script has a __main__ guard or direct common.run() call
            src_code = script_path.read_text(encoding="utf-8", errors="ignore")
            has_main_guard = "__main__" in src_code

            # Set clean sys.argv for the target script (pass 'all' for core/main.py)
            if script_path.name == "main.py":
                sys.argv = [str(script_path), "all"]
            else:
                sys.argv = [str(script_path)]

            start_t = time.time()
            # Execute file with __name__ == "__main__"
            mod_globals = runpy.run_path(str(script_path), run_name="__main__")

            # If the script didn't have a __main__ guard and finished quickly without launching a browser,
            # invoke its entry function (main / run / module function)
            if not has_main_guard and (time.time() - start_t < 2.5):
                stem = script_path.stem
                target_fn = None

                # 1. Check standard entry point names
                for cand in ["main", "run", stem, f"run_{stem}", f"test_{stem}"]:
                    if cand in mod_globals and callable(mod_globals[cand]):
                        target_fn = mod_globals[cand]
                        break

                # 2. Otherwise find the last public function defined inside this file
                if target_fn is None:
                    local_fns = [
                        obj
                        for name, obj in mod_globals.items()
                        if inspect.isfunction(obj)
                        and obj.__module__ == "__main__"
                        and not name.startswith("_")
                    ]
                    if local_fns:
                        target_fn = local_fns[-1]

                if target_fn is not None:
                    sig = inspect.signature(target_fn)
                    req_params = [
                        p
                        for p in sig.parameters.values()
                        if p.default is inspect.Parameter.empty
                        and p.kind
                        in (
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        )
                    ]

                    if len(req_params) == 0:
                        target_fn()
                    else:
                        # Function requires a logged-in Selenium driver from core
                        driver = None
                        try:
                            helpers = importlib.import_module("helpers")

                            for fn_name in [
                                "get_driver",
                                "init_driver",
                                "create_driver",
                                "setup_driver",
                            ]:
                                if hasattr(helpers, fn_name):
                                    driver = getattr(helpers, fn_name)()
                                    break
                        except Exception:
                            pass

                        if driver is None:
                            from selenium import webdriver

                            driver = webdriver.Chrome()
                            driver.maximize_window()

                        try:
                            if stem != "authentication":
                                authentication = importlib.import_module(
                                    "authentication"
                                )

                                for auth_fn_name in [
                                    "login",
                                    "authenticate",
                                    "run",
                                    "main",
                                    "authentication",
                                ]:
                                    if hasattr(authentication, auth_fn_name):
                                        auth_fn = getattr(
                                            authentication, auth_fn_name
                                        )
                                        if (
                                            len(
                                                inspect.signature(
                                                    auth_fn
                                                ).parameters
                                            )
                                            >= 1
                                        ):
                                            auth_fn(driver)
                                        else:
                                            res = auth_fn()
                                            if res is not None:
                                                driver = res
                                        break

                            if len(req_params) == 1:
                                target_fn(driver)
                            else:
                                from selenium.webdriver.support.ui import (
                                    WebDriverWait,
                                )

                                target_fn(driver, WebDriverWait(driver, 20))
                        finally:
                            try:
                                driver.quit()
                            except Exception:
                                pass

            sys.exit(0)
        except SystemExit as se:
            sys.exit(se.code if se.code is not None else 0)
        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)


# MODULE DEFINITIONS

MODULES = {
    "DMS": {
        "sheet_name": "DMS",
        "tests": [
            (
                "DMS-TC002",
                "tc002_document_attach.py",
                "Document Attach (18 file types)",
            ),
            (
                "DMS-TC003",
                "tc003_doc_view_grid.py",
                "Document View (Grid View)",
            ),
            (
                "DMS-TC009",
                "tc009_Upload_Document.py",
                "Upload Document (Required metadata)",
            ),
            (
                "DMS-TC011",
                "tc011_Multiple_pdf_merge.py",
                "Multiple PDF Merge",
            ),
            (
                "DMS-TC012",
                "tc012_document_name_convention.py",
                "Document Name Convention",
            ),
            (
                "DMS-TC014",
                "tc014_version_doc_upload.py",
                "Version Doc Upload",
            ),
            (
                "DMS-TC015",
                "tc015_download_version_doc.py",
                "Download Version Doc",
            ),
            (
                "DMS-TC016",
                "tc016_delete_version_doc.py",
                "Delete Version Doc",
            ),
            ("DMS-TC019", "tc019_edit_metadata.py", "Edit Metadata"),
            ("DMS-TC020", "tc020_check_out_doc.py", "Check-Out Document"),
            ("DMS-TC021", "tc021_cancel_checkout_doc.py", "Cancel Check-Out"),
            ("DMS-TC022", "tc022_download_document.py", "Download Document"),
            (
                "DMS-TC023",
                "tc023_multiple_doc_download.py",
                "Multiple Document Download (Zip)",
            ),
            (
                "DMS-TC024",
                "tc024_document_full_view.py",
                "Document Full View (New Tab)",
            ),
            ("DMS-TC025", "tc025_archive_doc.py", "Archive Document"),
            (
                "DMS-TC026",
                "tc026_restore_archived_doc.py",
                "Restore Archived Document",
            ),
            ("DMS-TC027", "tc027_delete_document.py", "Delete Document"),
            (
                "DMS-TC028",
                "tc028_restore_deleted_doc.py",
                "Restore Deleted Document",
            ),
            ("DMS-TC030", "tc030_add_related_files.py", "Add Related Files"),
            (
                "DMS-TC031",
                "tc031_delete_related_files.py",
                "Delete Related Files",
            ),
            (
                "DMS-TC032",
                "tc032_share_documents_users_groups_all.py",
                "Share Documents (Users/Groups/All)",
            ),
            (
                "DMS-TC033",
                "tc033_share_documents_external.py",
                "Share Documents (Public Share)",
            ),
            (
                "DMS-TC034",
                "tc034_share_documents_delete.py",
                "Share Documents (Delete Share)",
            ),
            (
                "DMS-TC036",
                "tc036_share_documents_email.py",
                "Share Documents (Email)",
            ),
            ("DMS-TC037", "tc037_document_ocr.py", "Document OCR"),
            (
                "DMS-TC042",
                "tc042_watermark_custom_text.py",
                "Watermark (Custom Text)",
            ),
            (
                "DMS-TC045",
                "tc045_watermark_upload.py",
                "Watermark (Upload File)",
            ),
            ("DMS-TC046", "tc046_search_water_mark.py", "Search Watermark"),
            (
                "DMS-TC049",
                "tc049_document_watermark.py",
                "Document Watermark (Attach)",
            ),
            ("DMS-TC050", "tc050_delete_watermark.py", "Delete Watermark"),
            ("DMS-TC051", "tc051_my_documents.py", "My Documents (Permissions)"),
            (
                "DMS-TC055",
                "tc055_grid_view_on_my_documents.py",
                "Grid View on My Documents",
            ),
            (
                "DMS-TC056",
                "tc056_list_view_on_my_documents.py",
                "List View on My Documents",
            ),
            (
                "DMS-TC057",
                "tc057_default_sorting_on_my_documents.py",
                "Default Sorting (Date Descending)",
            ),
            (
                "DMS-TC058",
                "tc058_sorting_name_ascending_on_my_documents.py",
                "Sorting (Name Ascending)",
            ),
            (
                "DMS-TC059",
                "tc059_sorting_name_descending_on_my_documents.py",
                "Sorting (Name Descending)",
            ),
            (
                "DMS-TC060",
                "tc060_sorting_date_ascending_on_my_documents.py",
                "Sorting (Date Ascending)",
            ),
            (
                "DMS-TC061",
                "tc061_sorting_date_descending_on_my_documents.py",
                "Sorting (Date Descending)",
            ),
            (
                "DMS-TC062",
                "tc062_default_sorting_category_doc_type.py",
                "Category Default Sorting",
            ),
            (
                "DMS-TC067",
                "tc067_categorization_doc_type_creation.py",
                "Doc-Type Creation",
            ),
            (
                "DMS-TC069",
                "tc069_update_category_doc_type.py",
                "Update Category/Doc-Type",
            ),
            (
                "DMS-TC073",
                "tc073_delete_category_doc_type.py",
                "Delete Category/Doc-Type",
            ),
            (
                "DMS-TC075",
                "tc075_deleted_category_map.py",
                "Deleted Category Map",
            ),
            (
                "DMS-TC076",
                "tc076_deleted_category_restore.py",
                "Deleted Category Restore",
            ),
            (
                "DMS-TC077",
                "tc077_deleted_category_permanent_deletion.py",
                "Deleted Category Permanent Delete",
            ),
            (
                "DMS-TC078",
                "tc078_deleted_category_full_path.py",
                "Deleted Category Full Path",
            ),
            ("DMS-TC080", "tc080_publish_doc_type.py", "Publish Doc-Type"),
            (
                "DMS-TC081",
                "tc081_assign_access_group_in_doc_type.py",
                "Assign Access Group",
            ),
            (
                "DMS-TC082",
                "tc082_assign_owner_group_in_doc_type.py",
                "Assign Owner Group",
            ),
            ("DMS-TC083", "tc083_document_notify_on.py", "Document Notify On"),
            (
                "DMS-TC084",
                "tc084_document_notify_off.py",
                "Document Notify Off",
            ),
            ("DMS-TC085", "tc085_create_metadata.py", "Create Metadata Field"),
            ("DMS-TC086", "tc086_update_metadata.py", "Update Metadata Field"),
            ("DMS-TC087", "tc087_delete_metadata.py", "Delete Metadata Field"),
            (
                "DMS-TC090",
                "tc090_metadata_uniqueness.py",
                "Metadata Uniqueness (Single)",
            ),
            (
                "DMS-TC091",
                "tc091_metadata_uniqueness_or.py",
                "Metadata Uniqueness (OR)",
            ),
            (
                "DMS-TC092",
                "tc092_metadata_uniqueness_and.py",
                "Metadata Uniqueness (AND)",
            ),
            (
                "DMS-TC093",
                "tc093_bulk_upload_template_download.py",
                "Bulk Upload Template Download",
            ),
            (
                "DMS-TC094",
                "tc094_bulk_upload_template_upload_invalid.py",
                "Bulk Upload Validation (Errors)",
            ),
            (
                "DMS-TC095",
                "tc095_bulk_upload_template_upload_valid.py",
                "Bulk Upload Valid Template",
            ),
            (
                "DMS-TC101",
                "tc101_master_table_method_fetch_multiple_record.py",
                "Master Table Method (Multiple Record)",
            ),
            (
                "DMS-TC102",
                "tc102_master_table_method_fetch_single_record.py",
                "Master Table Method (Single Record)",
            ),
            (
                "DMS-TC103",
                "tc103_master_table_method_update_multiple_record.py",
                "Master Table Method Update (Multiple)",
            ),
            (
                "DMS-TC104",
                "tc104_master_table_method_update_single_record.py",
                "Master Table Method Update (Single)",
            ),
            (
                "DMS-TC105",
                "tc105_master_table_method_delete.py",
                "Master Table Method Delete",
            ),
            (
                "DMS-TC106",
                "tc106_master_table_method_filter_by_doc_type.py",
                "Master Table Filter By Doc-Type",
            ),
            (
                "DMS-TC107",
                "tc107_master_table_method_search.py",
                "Master Table Method Search",
            ),
            (
                "DMS-TC108",
                "tc108_master_table_method_disable.py",
                "Master Table Method Disable",
            ),
            (
                "DMS-TC109",
                "tc109_master_table_method_enable.py",
                "Master Table Method Enable",
            ),
            (
                "DMS-TC110",
                "tc110_master_table_method_clone.py",
                "Master Table Method Clone",
            ),
            (
                "DMS-TC112",
                "tc112_master_table_method_assign.py",
                "Master Table Method Assign",
            ),
            ("DMS-TC119", "tc119_quick_search.py", "Quick Search"),
            (
                "DMS-TC121",
                "tc121_advanced_search_enable_match_all.py",
                "Advanced Search (Match All ON)",
            ),
            (
                "DMS-TC122",
                "tc122_advanced_search_disable_match_all.py",
                "Advanced Search (Match All OFF)",
            ),
            (
                "DMS-TC124",
                "tc124_advanced_search_enable_archive.py",
                "Advanced Search (Include Archive)",
            ),
            ("DMS-TC125", "tc125_save_search.py", "Save Advanced Search"),
            ("DMS-TC126", "tc126_saved_search_list.py", "Saved Search List"),
            (
                "DMS-TC127",
                "tc127_document_maker_checker_feature.py",
                "Maker-Checker Upload & Review",
            ),
            (
                "DMS-TC128",
                "tc128_pending_for_review_requested_by_me.py",
                "Pending Review: Requested By Me",
            ),
            (
                "DMS-TC130",
                "tc130_document_review_by_checker.py",
                "Pending Review: Checker Options",
            ),
            (
                "DMS-TC131",
                "tc131_document_approve_reject.py",
                "Document Approve & Reject",
            ),
            ("DMS-TC132", "tc132_bulk_upload.py", "Bulk Upload Large Files"),
            (
                "DMS-TC136",
                "tc136_pdf_document_ocr_from_advanced_search.py",
                "OCR Advanced Search",
            ),
            (
                "DMS-TC137",
                "tc137_pdf_document_ocr_from_my_documents_search.py",
                "OCR Explorer Search",
            ),
            (
                "DMS-TC139",
                "tc139_chat_with_pdf.py",
                "Chat With PDF (Ask Effy AI)",
            ),
        ],
    },
    "Core": {
        "sheet_name": "Core",
        "tests": [
            ("CORE-001", "core/authentication.py", "Authentication"),
            ("CORE-002", "core/announcement.py", "Announcement"),
            ("CORE-003", "core/branch_management.py", "Branch Management"),
            ("CORE-004", "core/department_management.py", "Department Management"),
            ("CORE-005", "core/group_management.py", "Group Management"),
            ("CORE-006", "core/role_management.py", "Role Management"),
            ("CORE-007", "core/user_management.py", "User Management"),
            ("CORE-008", "core/profile_update.py", "Profile Update"),
            ("CORE-009", "core/signature_management.py", "Signature Management"),
            ("CORE-010", "core/sign_up_request.py", "Sign Up Request"),
            ("CORE-011", "core/master_table_management.py", "Master Table Management"),
            (
                "CORE-012",
                "core/master_table_element_management.py",
                "Master Table Element Management",
            ),
            (
                "CORE-013",
                "core/master_table_record_management.py",
                "Master Table Record Management",
            ),
            ("CORE-014", "core/test_mail.py", "Test Mail Configuration"),
            ("CORE-ALL", "core/main.py", "Run Full Core Suite (main.py)"),
        ],
    },
    "Workflow": {
        "sheet_name": "Workflow",
        "tests": [],
    },
    "Report": {
        "sheet_name": "Report",
        "tests": [
            # Core Login Report
            (
                "REP-TC001",
                "report/rep001_core_login_report.py",
                "Core Login Report (General User - Own Scope)",
            ),
            (
                "REP-TC002",
                "report/rep002_core_login_report.py",
                "Core Login Report (Manager - All Users)",
            ),
            (
                "REP-TC003",
                "report/rep003_core_login_report.py",
                "Core Login Report (Search by User & IP)",
            ),
            (
                "REP-TC004",
                "report/rep004_core_login_report.py",
                "Core Login Report (Date Range Filter)",
            ),
            (
                "REP-TC005",
                "report/rep005_export_print_copy_login_report.py",
                "Core Login Report (Copy / CSV / Print)",
            ),
            # Core Activity Report
            (
                "REP-TC006",
                "report/rep006_core_activity_report.py",
                "Core Activity Report (General User - Own Scope)",
            ),
            (
                "REP-TC007",
                "report/rep007_core_activity_report.py",
                "Core Activity Report (Manager - All Users)",
            ),
            (
                "REP-TC008",
                "report/rep008_core_activity_report.py",
                "Core Activity Report (Verify Loaded Records)",
            ),
            (
                "REP-TC009",
                "report/rep009_core_activity_report.py",
                "Core Activity Report (Search by User & Operation)",
            ),
            (
                "REP-TC010",
                "report/rep010_core_activity_report.py",
                "Core Activity Report (Date Range Filter)",
            ),
            (
                "REP-TC011",
                "report/rep011_core_activity_report.py",
                "Core Activity Report (Column Sorting)",
            ),
            (
                "REP-TC012",
                "report/rep012_export_print_copy_login_report.py",
                "Core Activity Report (Copy / CSV / Print)",
            ),
            # Core API Report
            (
                "REP-TC013",
                "report/rep013_core_api_report.py",
                "Core API Report (General User - Access Denied)",
            ),
            (
                "REP-TC014",
                "report/rep014_core_api_report.py",
                "Core API Report (Manager - All API Logs)",
            ),
            (
                "REP-TC015",
                "report/rep015_core_api_report.py",
                "Core API Report (Search by URL / IP / Method / Status)",
            ),
            (
                "REP-TC016",
                "report/rep016_core_api_report.py",
                "Core API Report (Date Range Filter)",
            ),
            (
                "REP-TC017",
                "report/rep017_download_api_report.py",
                "Core API Report (Page Size & Copy / CSV / Print)",
            ),
            # DMS Activity Report
            (
                "REP-TC018",
                "report/rep018_dms_activity_report.py",
                "DMS Activity Report (General User - Own Scope)",
            ),
            (
                "REP-TC019",
                "report/rep019_dms_activity_report.py",
                "DMS Activity Report (Manager - All Users)",
            ),
            (
                "REP-TC020",
                "report/rep020_dms_activity_report.py",
                "DMS Activity Report (Search by User / Operation / IP)",
            ),
            (
                "REP-TC021",
                "report/rep021_dms_activity_report.py",
                "DMS Activity Report (Date Range Filter)",
            ),
            (
                "REP-TC022",
                "report/rep022_dms_activity_report.py",
                "DMS Activity Report (Filter by Operation & User)",
            ),
            (
                "REP-TC023",
                "report/rep023_export_print_copy_dms_activity_report.py",
                "DMS Activity Report (Copy / CSV / Excel / Print)",
            ),
            # Document Summary Report
            (
                "REP-TC024",
                "report/rep024_document_summary_report.py",
                "Document Summary Report (Admin / Permitted Access)",
            ),
            # Upload Record Report
            (
                "REP-TC025",
                "report/rep025_upload_record_report.py",
                "Upload Record Report (General User - Own Scope)",
            ),
            (
                "REP-TC026",
                "report/rep026_upload_record_report.py",
                "Upload Record Report (Manager - All Users)",
            ),
            (
                "REP-TC027",
                "report/rep027_upload_record_report.py",
                "Upload Record Report (Search by Uploader / Doc / Meta)",
            ),
            (
                "REP-TC028",
                "report/rep028_upload_record_report.py",
                "Upload Record Report (Date Range Filter)",
            ),
            (
                "REP-TC029",
                "report/rep029_upload_record_report.py",
                "Upload Record Report (Filter by Document Type)",
            ),
            (
                "REP-TC030",
                "report/rep030_export_upload_record_report.py",
                "Upload Record Report (Copy / CSV / Excel)",
            ),
            # Document Record Report
            (
                "REP-TC031",
                "report/rep031_document_record_report.py",
                "Document Record Report (General User - Group Scope)",
            ),
            (
                "REP-TC032",
                "report/rep032_document_record_report.py",
                "Document Record Report (Manager - All Doc Types)",
            ),
            (
                "REP-TC033",
                "report/rep033_document_record_report.py",
                "Document Record Report (Search by Uploader / Doc / Meta)",
            ),
            (
                "REP-TC034",
                "report/rep034_document_record_report.py",
                "Document Record Report (Date Range Filter)",
            ),
            (
                "REP-TC035",
                "report/rep035_document_record_report.py",
                "Document Record Report (Filter by Document Type)",
            ),
            (
                "REP-TC036",
                "report/rep036_export_document_record_report.py",
                "Document Record Report (Export Excel)",
            ),
            # Archived Document Record Report
            (
                "REP-TC037",
                "report/rep037_archived_document_record_report.py",
                "Archived Document Report (General User - Group Scope)",
            ),
            (
                "REP-TC038",
                "report/rep038_archived_document_record_report.py",
                "Archived Document Report (Manager - All Doc Types)",
            ),
            (
                "REP-TC039",
                "report/rep039_archived_document_record_report.py",
                "Archived Document Report (Search by Uploader / Doc / Meta)",
            ),
            (
                "REP-TC040",
                "report/rep040_archived_document_record_report.py",
                "Archived Document Report (Date Range Filter)",
            ),
            (
                "REP-TC041",
                "report/rep041_archived_document_record_report.py",
                "Archived Document Report (Filter by Document Type)",
            ),
            (
                "REP-TC042",
                "report/rep042_export_archived_document_record_report.py",
                "Archived Document Report (Export Excel)",
            ),
            # Document Type (Accessibility) Report
            (
                "REP-TC043",
                "report/rep043_document_type_accessibility_report.py",
                "Document Type Report (General User - Own Scope)",
            ),
            (
                "REP-TC044",
                "report/rep044_document_type_accessibility_report.py",
                "Document Type Report (Manager - All Users)",
            ),
            (
                "REP-TC045",
                "report/rep045_document_type_accessibility_report.py",
                "Document Type Report (Search by Type / Group / Path)",
            ),
            (
                "REP-TC047",
                "report/rep047_document_type_accessibility_report.py",
                "Document Type Report (Filter by Users)",
            ),
            (
                "REP-TC048",
                "report/rep048_export_document_type_accessibility_report.py",
                "Document Type Report (Export Excel)",
            ),
            # Page Count Report
            (
                "REP-TC049",
                "report/rep049_page_count_report.py",
                "Page Count Report (General User - Permitted Scope)",
            ),
            (
                "REP-TC050",
                "report/rep050_page_count_report.py",
                "Page Count Report (Manager - All Doc Types & Columns)",
            ),
            (
                "REP-TC051",
                "report/rep051_page_count_report.py",
                "Page Count Report (Search by Document Type)",
            ),
            (
                "REP-TC052",
                "report/rep052_page_count_report.py",
                "Page Count Report (Date Range Filter)",
            ),
            (
                "REP-TC053",
                "report/rep053_page_count_report.py",
                "Page Count Report (Filter by Document Type)",
            ),
            (
                "REP-TC054",
                "report/rep054_export_print_copy_page_count_report.py",
                "Page Count Report (Copy / CSV / Print)",
            ),
            # KPI Report
            (
                "REP-TC055",
                "report/rep055_kpi_report.py",
                "KPI Report (Unassigned User - Own Scope)",
            ),
            (
                "REP-TC056",
                "report/rep056_kpi_report.py",
                "KPI Report (Admin - All Users)",
            ),
            (
                "REP-TC057",
                "report/rep057_kpi_report.py",
                "KPI Report (Department Manager / HOD Scope)",
            ),
            (
                "REP-TC058",
                "report/rep058_kpi_report.py",
                "KPI Report (Department User - Own Scope)",
            ),
            (
                "REP-TC059",
                "report/rep059_kpi_report.py",
                "KPI Report (Search by User)",
            ),
            (
                "REP-TC060",
                "report/rep060_kpi_report.py",
                "KPI Report (Filter by User & Department)",
            ),
            (
                "REP-TC061",
                "report/rep061_kpi_report.py",
                "KPI Report (Date Range Filter)",
            ),
            (
                "REP-TC062",
                "report/rep062_export_kpi_report.py",
                "KPI Report (Direct Export < 100 Rows)",
            ),
            (
                "REP-TC063",
                "report/rep063_export_kpi_report.py",
                "KPI Report (Queued Export > 100 Rows)",
            ),
            # Task Activity Report
            (
                "REP-TC064",
                "report/rep064_task_activity_report.py",
                "Task Activity Report (General User - Own Scope)",
            ),
            (
                "REP-TC065",
                "report/rep065_task_activity_report.py",
                "Task Activity Report (Related Process User Scope)",
            ),
            (
                "REP-TC066",
                "report/rep066_task_activity_report.py",
                "Task Activity Report (All Process Info Scope)",
            ),
            (
                "REP-TC067",
                "report/rep067_task_activity_report.py",
                "Task Activity Report (Search by Project / App / User / Status)",
            ),
            (
                "REP-TC068",
                "report/rep068_task_activity_report.py",
                "Task Activity Report (Date Range Filter)",
            ),
            (
                "REP-TC069",
                "report/rep069_task_activity_report.py",
                "Task Activity Report (Filter by User)",
            ),
            (
                "REP-TC070",
                "report/rep070_task_activity_report.py",
                "Task Activity Report (Download Back End)",
            ),
            (
                "REP-TC071",
                "report/rep071_task_activity_report.py",
                "Task Activity Report (Download Front End)",
            ),
            # Application Activity Report
            (
                "REP-TC072",
                "report/rep072_application_activity_report.py",
                "Application Activity Report (General User - Own Scope)",
            ),
            (
                "REP-TC073",
                "report/rep073_application_activity_report.py",
                "Application Activity Report (Related Process User Scope)",
            ),
            (
                "REP-TC074",
                "report/rep074_application_activity_report.py",
                "Application Activity Report (All Process Info Scope)",
            ),
            (
                "REP-TC075",
                "report/rep075_application_activity_report.py",
                "Application Activity Report (Search by Project / App / User / Status)",
            ),
            (
                "REP-TC076",
                "report/rep076_application_activity_report.py",
                "Application Activity Report (Date Range Filter)",
            ),
            (
                "REP-TC077",
                "report/rep077_application_activity_report.py",
                "Application Activity Report (Download Back End)",
            ),
            (
                "REP-TC078",
                "report/rep078_application_activity_report.py",
                "Application Activity Report (Download Front End)",
            ),
            # Workflow Activity Report
            (
                "REP-TC079",
                "report/rep079_workflow_activity_report.py",
                "Workflow Activity Report (General User - Own Scope)",
            ),
            (
                "REP-TC080",
                "report/rep080_workflow_activity_report.py",
                "Workflow Activity Report (Related Process User Scope)",
            ),
            (
                "REP-TC081",
                "report/rep081_workflow_activity_report.py",
                "Workflow Activity Report (All Process Info Scope)",
            ),
            (
                "REP-TC082",
                "report/rep082_workflow_activity_report.py",
                "Workflow Activity Report (Search by User / Operation / IP)",
            ),
            (
                "REP-TC083",
                "report/rep083_workflow_activity_report.py",
                "Workflow Activity Report (Filter by Process)",
            ),
            (
                "REP-TC084",
                "report/rep084_workflow_activity_report.py",
                "Workflow Activity Report (Date Range Filter)",
            ),
            (
                "REP-TC085",
                "report/rep085_workflow_activity_report.py",
                "Workflow Activity Report (Download Back End)",
            ),
            (
                "REP-TC086",
                "report/rep086_workflow_activity_report.py",
                "Workflow Activity Report (Download Front End)",
            ),
            # Custom Report
            (
                "REP-TC087",
                "report/rep087_custom_report.py",
                "Custom Report (General User - Own Scope)",
            ),
            (
                "REP-TC088",
                "report/rep088_custom_report.py",
                "Custom Report (Related Process User Scope)",
            ),
            (
                "REP-TC089",
                "report/rep089_custom_report.py",
                "Custom Report (All Process Info Scope)",
            ),
            (
                "REP-TC090",
                "report/rep090_custom_report.py",
                "Custom Report (Search by App / User / Status)",
            ),
            (
                "REP-TC091",
                "report/rep091_custom_report.py",
                "Custom Report (Date Range Filter)",
            ),
            (
                "REP-TC092",
                "report/rep092_custom_report.py",
                "Custom Report (Filter by Status & Initiator)",
            ),
            (
                "REP-TC093",
                "report/rep093_custom_report.py",
                "Custom Report (Download Back End)",
            ),
            (
                "REP-TC094",
                "report/rep094_custom_report.py",
                "Custom Report (Download Front End)",
            ),
            # Auto Approval Report
            (
                "REP-TC095",
                "report/rep095_auto_approval_report.py",
                "Auto Approval Report (General User - Own Scope)",
            ),
            (
                "REP-TC096",
                "report/rep096_auto_approval_report.py",
                "Auto Approval Report (Related Process User Scope)",
            ),
            (
                "REP-TC097",
                "report/rep097_auto_approval_report.py",
                "Auto Approval Report (All Process Info Scope)",
            ),
            (
                "REP-TC098",
                "report/rep098_auto_approval_report.py",
                "Auto Approval Report (Search by Project / App / User)",
            ),
            (
                "REP-TC099",
                "report/rep099_auto_approval_report.py",
                "Auto Approval Report (Column Sorting)",
            ),
            (
                "REP-TC100",
                "report/rep100_auto_approval_report.py",
                "Auto Approval Report (Date Range Filter)",
            ),
            (
                "REP-TC101",
                "report/rep101_auto_approval_report.py",
                "Auto Approval Report (Filter by Process & User)",
            ),
            (
                "REP-TC102",
                "report/rep102_auto_approval_report.py",
                "Auto Approval Report (Export CSV / Excel)",
            ),
        ],
    },
    "Configurable": {
        "sheet_name": "Configurable",
        "tests": [],
    },
}

DROPDOWN_OPTIONS = ["ALL"] + list(MODULES.keys())


# MAIN GUI APPLICATION

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # hides console flashes
LOGO_HEIGHTS = (40, 50, 60, 70, 80)  # pre-sized logos in assets/ (100%..200% DPI)

CHECKED = "☑"
UNCHECKED = "☐"

STATUS_TEXT = {
    "pending": "—",
    "running": "● Running",
    "pass": "✔ Pass",
    "fail": "✘ Fail",
    "stopped": "■ Stopped",
}


class AutomationRunnerGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Robo2mation Automated QA Test Runner v6.0")
        self.geometry("1220x800")
        self.minsize(980, 640)
        self._set_window_icon()

        # Scale factor so sizes look right on high-DPI screens
        self.scale = self.winfo_fpixels("1i") / 96

        self.is_running = False
        self.stop_requested = False
        self.ui_queue = queue.Queue()  # worker thread -> UI thread messages
        self.current_process = None
        self.allure_server = None

        # Data for the selected module and cross-module tracking for charts
        self.tests = []  # [(test_id, script_name, description, mod_name, sheet_name)]
        self.selected = {}  # script_name -> True / False
        self.results = {}  # script_name -> (status, duration_text)
        self.module_results = {m: {} for m in MODULES}  # module_name -> {script: (status, duration_sec, test_id)}
        self.execution_history = []  # [(test_id, duration_sec, status, module_name)]

        self._setup_styles()
        self._build_header()
        self._build_config_bar()
        self._build_status_footer()  # footer first, so it never gets cut off
        self._build_main_split()
        self._load_module(self.module_var.get())

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._process_ui_queue)

    def _set_window_icon(self):
        icon = find_script_path("assets/app.ico")
        if icon:
            try:
                self.iconbitmap(str(icon))
            except Exception:
                pass

    # Styles

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Color Palette
        self.bg_color = "#F8FAFC"
        self.card_bg = "#FFFFFF"
        self.border_color = "#E2E8F0"
        self.primary_color = "#1992D0"  # blue from the Robo2 logo
        self.brand_dark = "#0E7AB5"  # darker shade for text (better contrast)
        self.header_bg = "#FFFFFF"

        self.configure(bg=self.bg_color)

        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("White.TFrame", background=self.card_bg)
        self.style.configure(
            "Card.TLabel",
            background=self.card_bg,
            foreground="#334155",
            font=("Segoe UI", 9),
        )

        # Cards
        self.style.configure(
            "Card.TLabelframe",
            background=self.card_bg,
            relief="solid",
            borderwidth=1,
            bordercolor=self.border_color,
        )
        self.style.configure(
            "Card.TLabelframe.Label",
            background=self.card_bg,
            font=("Segoe UI", 10, "bold"),
            foreground="#1E293B",
        )

        # Header
        self.style.configure("Header.TFrame", background=self.header_bg)
        self.style.configure(
            "Header.TLabel", background=self.header_bg, foreground="#0F172A"
        )

        # Notebook (Tabs)
        self.style.configure(
            "TNotebook",
            background=self.card_bg,
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 5),
            background="#F1F5F9",
            foreground="#475569",
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.primary_color), ("active", "#E2E8F0")],
            foreground=[("selected", "#FFFFFF"), ("active", "#1E293B")],
        )

        # Buttons
        self.style.configure(
            "Run.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#10B981",
            foreground="#FFFFFF",
            borderwidth=0,
            padding=(12, 6),
        )
        self.style.map(
            "Run.TButton",
            background=[("active", "#059669"), ("disabled", "#94A3B8")],
        )

        self.style.configure(
            "Stop.TButton",
            font=("Segoe UI", 10, "bold"),
            background="#EF4444",
            foreground="#FFFFFF",
            borderwidth=0,
            padding=(12, 6),
        )
        self.style.map(
            "Stop.TButton",
            background=[("active", "#DC2626"), ("disabled", "#94A3B8")],
        )

        self.style.configure(
            "Allure.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.primary_color,
            foreground="#FFFFFF",
            borderwidth=0,
            padding=(12, 6),
        )
        self.style.map(
            "Allure.TButton",
            background=[("active", self.brand_dark), ("disabled", "#94A3B8")],
        )

        self.style.configure(
            "Tool.TButton",
            font=("Segoe UI", 9),
            background="#F1F5F9",
            foreground="#1E293B",
            borderwidth=1,
            padding=(6, 3),
        )
        self.style.map("Tool.TButton", background=[("active", "#E2E8F0")])

        # Test list (Treeview)
        def fixed_map(option):
            # Fix for a Tk bug where row tag colors are ignored
            return [
                e
                for e in self.style.map("Treeview", query_opt=option)
                if e[:2] != ("!disabled", "!selected")
            ]

        self.style.configure(
            "Treeview",
            background=self.card_bg,
            fieldbackground=self.card_bg,
            foreground="#1E293B",
            rowheight=int(26 * self.scale),
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#D9EEF9")] + fixed_map("background"),
            foreground=[("selected", "#0F172A")] + fixed_map("foreground"),
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#F1F5F9",
            foreground="#1E293B",
            relief="flat",
        )
        self.style.map("Treeview.Heading", background=[("active", "#E2E8F0")])

        # Progress bar
        self.style.configure(
            "Blue.Horizontal.TProgressbar",
            troughcolor="#E2E8F0",
            background=self.primary_color,
            borderwidth=0,
            thickness=10,
        )

    # Layout
    
    def _load_logo(self):
        """Pick the pre-sized logo closest to the screen scale (no Pillow needed)."""
        target = 40 * self.scale
        height = min(LOGO_HEIGHTS, key=lambda h: abs(h - target))
        path = find_script_path(f"assets/robo2_logo_{height}.png")
        if not path:
            return None
        try:
            return tk.PhotoImage(file=str(path))
        except tk.TclError:
            return None

    def _build_header(self):
        # White header: the dark-grey logo would disappear on a dark background
        header = ttk.Frame(self, style="Header.TFrame", padding=(24, 12))
        header.pack(fill=tk.X, side=tk.TOP)

        self.logo_img = self._load_logo()  # keep a reference or Tk drops it
        if self.logo_img:
            ttk.Label(header, image=self.logo_img, style="Header.TLabel").pack(
                side=tk.LEFT
            )
            tk.Frame(header, width=1, bg=self.border_color).pack(
                side=tk.LEFT, fill=tk.Y, padx=18, pady=4
            )
            title_text = "Automated Sanity Suite"
        else:
            title_text = "Robo2mation Automated Sanity Suite"

        text_box = ttk.Frame(header, style="Header.TFrame")
        text_box.pack(side=tk.LEFT)
        ttk.Label(
            text_box,
            text=title_text,
            font=("Segoe UI", 16, "bold"),
            style="Header.TLabel",
        ).pack(anchor=tk.W)
        ttk.Label(
            text_box,
            text="Select module, review target test cases, and execute with live browser monitoring.",
            font=("Segoe UI", 9),
            foreground="#64748B",
            style="Header.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        tk.Label(
            header,
            text="v6.0",
            bg="#E8F4FB",
            fg=self.brand_dark,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        ).pack(side=tk.RIGHT)

        # Thin brand-colored line under the header
        tk.Frame(self, height=int(3 * self.scale), bg=self.primary_color).pack(
            fill=tk.X, side=tk.TOP
        )

    def _build_config_bar(self):
        bar = ttk.LabelFrame(
            self,
            text=" Configuration & Target Module ",
            style="Card.TLabelframe",
            padding=(16, 12),
        )
        bar.pack(fill=tk.X, padx=16, pady=(12, 6))

        # Module dropdown (includes "ALL")
        ttk.Label(
            bar,
            text="Module / Sheet:",
            font=("Segoe UI", 9, "bold"),
            background=self.card_bg,
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 6), pady=4)
        self.module_var = tk.StringVar(value="DMS")
        self.module_dropdown = ttk.Combobox(
            bar,
            textvariable=self.module_var,
            values=DROPDOWN_OPTIONS,
            state="readonly",
            width=14,
            font=("Segoe UI", 9),
        )
        self.module_dropdown.grid(
            row=0, column=1, sticky=tk.W, padx=(0, 24), pady=4
        )
        self.module_dropdown.bind("<<ComboboxSelected>>", self._on_module_changed)

        # Excel file (Honor EXCEL_PATH from .env when available; fall back to local copy)
        ttk.Label(
            bar,
            text="Test Case Excel:",
            font=("Segoe UI", 9, "bold"),
            background=self.card_bg,
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 6), pady=4)
        self.excel_var = tk.StringVar(value=_resolve_default_excel())
        ttk.Entry(
            bar, textvariable=self.excel_var, width=44, font=("Segoe UI", 9)
        ).grid(row=0, column=3, sticky=tk.EW, padx=(0, 8), pady=4)

        ttk.Button(
            bar,
            text="Browse...",
            command=self._browse_excel,
            style="Tool.TButton",
            width=9,
        ).grid(row=0, column=4, sticky=tk.W, padx=(0, 6), pady=4)

        ttk.Button(
            bar,
            text="Open",
            command=self._open_excel,
            style="Tool.TButton",
            width=7,
        ).grid(row=0, column=5, sticky=tk.W, pady=4)

        bar.columnconfigure(3, weight=1)

    def _build_status_footer(self):
        footer = ttk.Frame(self, padding=(16, 10))
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress_bar = ttk.Progressbar(
            footer,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="Blue.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 6))

        stats_box = ttk.Frame(footer)
        stats_box.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_lbl = ttk.Label(
            stats_box,
            text="Ready to run.",
            font=("Segoe UI", 9, "italic"),
            foreground="#64748B",
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.summary_lbl = ttk.Label(
            stats_box,
            text="Total: 0  |  Passed: 0  |  Failed: 0",
            font=("Segoe UI", 9, "bold"),
            foreground="#1E293B",
        )
        self.summary_lbl.pack(side=tk.RIGHT)

    def _build_main_split(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=16, pady=6)
        self.paned = paned

        self._build_test_list(paned)
        self._build_output_panel(paned)
        self.after(150, self._set_default_sash)

    def _set_default_sash(self):
        """Give the test list about 46% of the window so both panels look balanced."""
        try:
            self.paned.sashpos(0, int(self.winfo_width() * 0.46))
        except tk.TclError:
            pass

    def _build_test_list(self, paned):
        left = ttk.LabelFrame(
            paned,
            text=" Available Test Cases ",
            style="Card.TLabelframe",
            padding=(12, 10),
        )
        paned.add(left, weight=5)

        # Search box
        search_row = ttk.Frame(left, style="White.TFrame")
        search_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_row, text="Search:", style="Card.TLabel").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_tree())
        ttk.Entry(search_row, textvariable=self.search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # Select buttons
        btn_row = ttk.Frame(left, style="White.TFrame")
        btn_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(
            btn_row,
            text="Select All",
            command=lambda: self._set_visible_checked(True),
            style="Tool.TButton",
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn_row,
            text="Deselect All",
            command=lambda: self._set_visible_checked(False),
            style="Tool.TButton",
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn_row,
            text="Select Failed",
            command=self._select_failed,
            style="Tool.TButton",
        ).pack(side=tk.LEFT)

        # Counter (packed before the list so it is always visible)
        self.counter_lbl = ttk.Label(left, text="", style="Card.TLabel")
        self.counter_lbl.pack(side=tk.BOTTOM, anchor=tk.W, pady=(8, 0))

        # Test table
        tree_wrap = ttk.Frame(left, style="White.TFrame")
        tree_wrap.pack(fill=tk.BOTH, expand=True)

        px = lambda v: int(v * self.scale)
        self.tree = ttk.Treeview(
            tree_wrap,
            columns=("sel", "id", "name", "status", "time"),
            show="headings",
            selectmode="extended",
        )
        self.tree.heading("sel", text="")
        self.tree.heading("id", text="Test ID")
        self.tree.heading("name", text="Description")
        self.tree.heading("status", text="Status")
        self.tree.heading("time", text="Time")
        self.tree.column("sel", width=px(36), minwidth=px(36), stretch=False, anchor=tk.CENTER)
        self.tree.column("id", width=px(85), minwidth=px(80), stretch=False)
        self.tree.column("name", width=px(180), minwidth=px(120), stretch=True)
        self.tree.column("status", width=px(90), minwidth=px(80), stretch=False)
        self.tree.column("time", width=px(55), minwidth=px(50), stretch=False, anchor=tk.E)

        scrollbar = ttk.Scrollbar(
            tree_wrap, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Row colors by status
        self.tree.tag_configure("pending", foreground="#1E293B")
        self.tree.tag_configure("running", foreground=self.brand_dark)
        self.tree.tag_configure("pass", foreground="#059669")
        self.tree.tag_configure("fail", foreground="#DC2626")
        self.tree.tag_configure("stopped", foreground="#D97706")

        # Click the checkbox column (or press Space) to tick / untick
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<space>", self._on_tree_space)

    def _build_output_panel(self, paned):
        right = ttk.LabelFrame(
            paned,
            text=" Execution Output & Analytics ",
            style="Card.TLabelframe",
            padding=(12, 10),
        )
        paned.add(right, weight=5)

        ctrl_box = ttk.Frame(right, style="White.TFrame")
        ctrl_box.pack(fill=tk.X, pady=(0, 10))

        self.run_btn = ttk.Button(
            ctrl_box,
            text="►  Run Tests",
            style="Run.TButton",
            command=self._start_run,
            width=12,
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(
            ctrl_box,
            text="■  Stop",
            style="Stop.TButton",
            command=self._stop_run,
            state=tk.DISABLED,
            width=8,
        )
        self.stop_btn.pack(side=tk.LEFT)

        self.allure_btn = ttk.Button(
            ctrl_box,
            text="📊 Allure Report",
            style="Allure.TButton",
            command=self._open_allure_report,
            width=16,
        )
        self.allure_btn.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Button(
            ctrl_box,
            text="Clear Log",
            style="Tool.TButton",
            command=self._clear_logs,
            width=8,
        ).pack(side=tk.RIGHT)
        ttk.Button(
            ctrl_box,
            text="Save Log",
            style="Tool.TButton",
            command=self._save_log,
            width=8,
        ).pack(side=tk.RIGHT, padx=(0, 6))

        # Tabbed interface: Console Log + Charts & Analytics
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Console Log
        log_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(log_tab, text="  Console Log  ")

        self.log_text = ScrolledText(
            log_tab,
            wrap=tk.WORD,
            bg="#0B132B",
            fg="#E0E1DD",
            insertbackground="#48CAE4",
            font=("Consolas", 10),
            padx=10,
            pady=10,
            borderwidth=0,
            relief="flat",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("pass", foreground="#34D399")
        self.log_text.tag_config("fail", foreground="#F87171")
        self.log_text.tag_config("warn", foreground="#FBBF24")
        self.log_text.tag_config("info", foreground="#48CAE4")

        # Tab 2: Charts & Analytics
        charts_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(charts_tab, text="  📊 Charts & Analytics  ")
        self._build_charts_tab(charts_tab)

    def _build_charts_tab(self, parent):
        """Creates a scrollable canvas that renders the Table, Pie Chart, and Timing Line Graph."""
        canvas_wrap = ttk.Frame(parent, style="White.TFrame")
        canvas_wrap.pack(fill=tk.BOTH, expand=True)

        self.charts_canvas = tk.Canvas(
            canvas_wrap,
            bg="#FFFFFF",
            highlightthickness=0,
        )
        v_scroll = ttk.Scrollbar(
            canvas_wrap, orient=tk.VERTICAL, command=self.charts_canvas.yview
        )
        self.charts_canvas.configure(yscrollcommand=v_scroll.set)

        self.charts_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.charts_canvas.bind("<Configure>", lambda e: self._refresh_charts())
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._refresh_charts())

    # Chart Drawing Engine (Table + Pie Chart + Timing Line Graph)
    
    def _refresh_charts(self):
        if not hasattr(self, "charts_canvas"):
            return
        c = self.charts_canvas
        c.delete("all")

        w = max(c.winfo_width(), int(520 * self.scale))
        pad = int(16 * self.scale)

        # 1. Draw Summary Table (Top Left) & Pie Chart (Top Right)
        y_cursor = int(14 * self.scale)
        half_w = (w - 3 * pad) // 2

        table_bottom = self._draw_summary_table(c, pad, y_cursor, half_w)
        pie_bottom = self._draw_pie_chart(c, pad * 2 + half_w, y_cursor, half_w)

        y_cursor = max(table_bottom, pie_bottom) + int(22 * self.scale)

        # Divider line
        c.create_line(pad, y_cursor, w - pad, y_cursor, fill="#E2E8F0", width=1)
        y_cursor += int(16 * self.scale)

        # 2. Draw Execution Timing Line Graph (Bottom Full Width)
        graph_h = int(250 * self.scale)
        graph_bottom = self._draw_timing_line_chart(
            c, pad, y_cursor, w - 2 * pad, graph_h
        )

        total_h = graph_bottom + int(20 * self.scale)
        c.configure(scrollregion=(0, 0, w, total_h))

    def _draw_summary_table(self, c: tk.Canvas, x: int, y: int, width: int) -> int:
        """Draws the Excel-style Pass/Fail summary table across modules."""
        s = self.scale
        c.create_text(
            x + width // 2,
            y + int(10 * s),
            text="Module Execution Summary",
            font=("Segoe UI", 11, "bold"),
            fill="#1E293B",
        )
        y_top = y + int(28 * s)

        # Display names matching user's Excel table ("Admin" maps to "Core")
        display_rows = [
            ("Admin", "Core"),
            ("Workflow", "Workflow"),
            ("DMS", "DMS"),
            ("Report", "Report"),
        ]

        row_h = int(25 * s)
        col0_w = int(width * 0.43)
        num_w = (width - col0_w) // 3
        col_widths = [col0_w, num_w, num_w, width - col0_w - 2 * num_w]

        def draw_cell(cx, cy, cw, ch, bg, text, font, fg="#000000", align="center"):
            c.create_rectangle(cx, cy, cx + cw, cy + ch, fill=bg, outline="#000000", width=1)
            if align == "left":
                c.create_text(
                    cx + int(6 * s), cy + ch // 2, text=text, font=font, fill=fg, anchor=tk.W
                )
            elif align == "right":
                c.create_text(
                    cx + cw - int(6 * s), cy + ch // 2, text=text, font=font, fill=fg, anchor=tk.E
                )
            else:
                c.create_text(
                    cx + cw // 2, cy + ch // 2, text=text, font=font, fill=fg, anchor=tk.CENTER
                )

        # Header Row
        headers = ["", "Total", "Pass", "Fail"]
        cur_x = x
        for idx, h_text in enumerate(headers):
            bg = "#FFFFFF" if idx == 0 else "#F8CBAD"
            draw_cell(
                cur_x,
                y_top,
                col_widths[idx],
                row_h,
                bg,
                h_text,
                ("Segoe UI", 9, "bold"),
                align="left" if idx > 0 else "center",
            )
            cur_x += col_widths[idx]

        # Module Rows
        cur_y = y_top + row_h
        grand_total = 0
        grand_pass = 0
        grand_fail = 0

        for label_name, mod_key in display_rows:
            mod_res = self.module_results.get(mod_key, {})
            p_cnt = sum(1 for st, _, _ in mod_res.values() if st == "pass")
            f_cnt = sum(1 for st, _, _ in mod_res.values() if st == "fail")
            t_cnt = p_cnt + f_cnt

            grand_total += t_cnt
            grand_pass += p_cnt
            grand_fail += f_cnt

            vals = [label_name, str(t_cnt), str(p_cnt), str(f_cnt)]
            cur_x = x
            for idx, val in enumerate(vals):
                bg = "#92CDDC" if idx == 0 else "#D9D9D9"
                fnt = ("Segoe UI", 9, "bold") if idx == 0 else ("Segoe UI", 9)
                align = "left" if idx == 0 else "right"
                draw_cell(cur_x, cur_y, col_widths[idx], row_h, bg, val, fnt, align=align)
                cur_x += col_widths[idx]
            cur_y += row_h

        # "In Total" Row
        totals_row = ["In Total", str(grand_total), str(grand_pass), str(grand_fail)]
        cur_x = x
        for idx, val in enumerate(totals_row):
            bg = "#92CDDC" if idx == 0 else "#D9D9D9"
            fnt = ("Segoe UI", 9, "bold") if idx == 0 else ("Segoe UI", 9)
            align = "left" if idx == 0 else "right"
            draw_cell(cur_x, cur_y, col_widths[idx], row_h, bg, val, fnt, align=align)
            cur_x += col_widths[idx]
        cur_y += row_h

        # "Pass Fail Ratio (in percentages)" Row (spans first two columns)
        pass_pct = (grand_pass / grand_total * 100.0) if grand_total > 0 else 0.0
        fail_pct = (grand_fail / grand_total * 100.0) if grand_total > 0 else 0.0

        span_w = col_widths[0] + col_widths[1]
        draw_cell(
            x,
            cur_y,
            span_w,
            row_h,
            "#92CDDC",
            "Pass Fail Ratio (in percentages)",
            ("Segoe UI", 8, "bold"),
            align="center",
        )
        draw_cell(
            x + span_w,
            cur_y,
            col_widths[2],
            row_h,
            "#E2EFDA",
            f"{pass_pct:.2f}%",
            ("Segoe UI", 9),
            align="right",
        )
        draw_cell(
            x + span_w + col_widths[2],
            cur_y,
            col_widths[3],
            row_h,
            "#FF9999",
            f"{fail_pct:.2f}%",
            ("Segoe UI", 9),
            align="right",
        )

        return cur_y + row_h

    def _draw_pie_chart(self, c: tk.Canvas, x: int, y: int, width: int) -> int:
        """Draws the Pass/Fail/Stopped distribution pie chart with percentage callout lines."""
        s = self.scale
        c.create_text(
            x + width // 2,
            y + int(10 * s),
            text="Pass / Fail Distribution",
            font=("Segoe UI", 11, "bold"),
            fill="#1D2A73",
        )

        # Aggregate counts from current view
        passed = sum(1 for st, _ in self.results.values() if st == "pass")
        failed = sum(1 for st, _ in self.results.values() if st == "fail")
        stopped = sum(1 for st, _ in self.results.values() if st == "stopped")
        total = passed + failed + stopped

        cx = x + width // 2
        cy = y + int(112 * s)
        radius = int(min(width * 0.28, 68 * s))

        if total == 0:
            c.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill="#F1F5F9",
                outline="#CBD5E1",
                width=2,
            )
            c.create_text(
                cx,
                cy,
                text="No Runs Yet",
                font=("Segoe UI", 9, "italic"),
                fill="#64748B",
            )
            return cy + radius + int(25 * s)

        slices = [
            ("Pass", passed, "#22A6DF"),
            ("Fail", failed, "#EF4444"),
            ("Stopped", stopped, "#8B5CF6"),
        ]
        active_slices = [(lbl, val, col) for lbl, val, col in slices if val > 0]

        start_angle = 90.0
        for lbl, val, col in active_slices:
            pct = (val / total) * 100.0
            extent = (val / total) * 360.0

            if len(active_slices) == 1:
                c.create_oval(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    fill=col,
                    outline="#FFFFFF",
                    width=1,
                )
                mid_angle = 45.0
            else:
                c.create_arc(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    start=start_angle,
                    extent=-extent,
                    fill=col,
                    outline="#FFFFFF",
                    width=1,
                )
                mid_angle = start_angle - extent / 2.0

            # Callout leader line and label
            rad = math.radians(mid_angle)
            x1 = cx + radius * math.cos(rad)
            y1 = cy - radius * math.sin(rad)
            x2 = cx + (radius + int(14 * s)) * math.cos(rad)
            y2 = cy - (radius + int(14 * s)) * math.sin(rad)

            horiz_dir = 1 if math.cos(rad) >= 0 else -1
            x3 = x2 + horiz_dir * int(12 * s)

            c.create_line(x1, y1, x2, y2, x3, y2, fill="#475569", width=1)
            c.create_text(
                x3 + horiz_dir * int(4 * s),
                y2,
                text=f"{lbl}\n{pct:.1f}%",
                font=("Segoe UI", 8, "bold"),
                fill="#334155",
                anchor=tk.W if horiz_dir > 0 else tk.E,
                justify=tk.CENTER,
            )

            start_angle -= extent

        return cy + radius + int(28 * s)

    def _draw_timing_line_chart(
        self, c: tk.Canvas, x: int, y: int, width: int, height: int
    ) -> int:
        """Draws the Execution Timing line graph with dashed gridlines and circular nodes."""
        s = self.scale
        c.create_text(
            x + width // 2,
            y + int(10 * s),
            text="Execution Timing (Seconds per Test Case)",
            font=("Segoe UI", 12, "bold"),
            fill="#0F172A",
        )

        left_pad = int(52 * s)
        right_pad = int(20 * s)
        top_pad = int(34 * s)
        bottom_pad = int(52 * s)

        plot_x0 = x + left_pad
        plot_y0 = y + top_pad
        plot_x1 = x + width - right_pad
        plot_y1 = y + height - bottom_pad
        plot_w = max(plot_x1 - plot_x0, 100)
        plot_h = max(plot_y1 - plot_y0, 80)

        # Y-axis label
        c.create_text(
            x + int(12 * s),
            (plot_y0 + plot_y1) // 2,
            text="Time (s)",
            font=("Segoe UI", 9, "bold"),
            fill="#334155",
            angle=90,
        )

        # X-axis title
        c.create_text(
            (plot_x0 + plot_x1) // 2,
            y + height - int(8 * s),
            text="Executed Test Cases",
            font=("Segoe UI", 9, "bold"),
            fill="#334155",
        )

        data = self.execution_history[-15:]  # Show up to last 15 executed tests cleanly
        max_val = max([d[1] for d in data], default=10.0)
        # Round ceiling up to a clean step divisible by 4
        y_max = max(math.ceil(max_val / 4.0) * 4.0, 4.0)

        # Horizontal dashed grid lines + Y-axis labels
        steps = 4
        for i in range(steps + 1):
            val = (y_max / steps) * i
            gy = plot_y1 - (i / steps) * plot_h
            c.create_line(
                plot_x0,
                gy,
                plot_x1,
                gy,
                fill="#E2E8F0",
                dash=(4, 4),
            )
            c.create_text(
                plot_x0 - int(8 * s),
                gy,
                text=f"{val:.0f}s",
                font=("Segoe UI", 8),
                fill="#334155",
                anchor=tk.E,
            )

        # Vertical dashed grid lines + Data coordinates
        points = []
        n = len(data)
        for idx, (tid, dur, status, _) in enumerate(data):
            if n == 1:
                px = plot_x0 + plot_w / 2
            else:
                px = plot_x0 + (idx / (n - 1)) * plot_w
            py = plot_y1 - (min(dur, y_max) / y_max) * plot_h
            points.append((px, py, tid, dur, status))

            c.create_line(
                px,
                plot_y0,
                px,
                plot_y1,
                fill="#E2E8F0",
                dash=(4, 4),
            )
            short_id = (
                tid.replace("DMS-", "")
                .replace("CORE-", "C-")
                .replace("REP-TC", "R-")
                .replace("REP-", "R-")
            )
            c.create_text(
                px,
                plot_y1 + int(14 * s),
                text=short_id,
                font=("Segoe UI", 8),
                fill="#0F172A",
            )

        # Solid Axes
        c.create_line(plot_x0, plot_y0, plot_x0, plot_y1, fill="#64748B", width=2)
        c.create_line(plot_x0, plot_y1, plot_x1, plot_y1, fill="#64748B", width=2)

        if not points:
            c.create_text(
                (plot_x0 + plot_x1) // 2,
                (plot_y0 + plot_y1) // 2,
                text="Run test cases to plot live execution timing",
                font=("Segoe UI", 9, "italic"),
                fill="#64748B",
            )
            return y + height

        # Connecting line segments
        for i in range(len(points) - 1):
            c.create_line(
                points[i][0],
                points[i][1],
                points[i + 1][0],
                points[i + 1][1],
                fill="#2C6B82",
                width=2,
            )

        # Hollow circular data markers + duration labels
        r = int(4 * s)
        for px, py, tid, dur, status in points:
            outline_col = "#DC2626" if status == "fail" else "#2C6B82"
            c.create_oval(
                px - r,
                py - r,
                px + r,
                py + r,
                fill="#FFFFFF",
                outline=outline_col,
                width=2,
            )
            c.create_text(
                px,
                py - int(10 * s),
                text=f"{dur:.1f}s",
                font=("Segoe UI", 7, "bold"),
                fill=outline_col,
            )

        return y + height

    # Test list handling (Supports "ALL" or individual modules)

    def _get_tests_for_selection(self, module_name: str):
        """Returns list of (test_id, script, desc, home_module, sheet_name)."""
        if module_name == "ALL":
            combined = []
            for mod_key, mod_data in MODULES.items():
                sheet = mod_data.get("sheet_name", mod_key)
                for tid, script, desc in mod_data.get("tests", []):
                    if tid == "CORE-ALL":
                        continue
                    combined.append((tid, script, f"[{mod_key}] {desc}", mod_key, sheet))
            return combined
        else:
            mod_data = MODULES.get(module_name, {})
            sheet = mod_data.get("sheet_name", module_name)
            return [
                (tid, script, desc, module_name, sheet)
                for tid, script, desc in mod_data.get("tests", [])
            ]

    def _load_module(self, module_name):
        self.tests = self._get_tests_for_selection(module_name)
        self.selected = {script: True for _, script, _, _, _ in self.tests}

        # Restore any previous results for the visible tests
        self.results = {}
        for _, script, _, home_mod, _ in self.tests:
            saved = self.module_results.get(home_mod, {})
            if script in saved:
                st, dur, _ = saved[script]
                self.results[script] = (st, f"{dur:.1f}s" if dur > 0 else "")

        self.search_var.set("")
        self._refresh_tree()
        self._refresh_charts()

    def _refresh_tree(self):
        """Rebuild the table, applying the search filter."""
        self.tree.delete(*self.tree.get_children())
        term = self.search_var.get().strip().lower()

        for test_id, script, desc, _, _ in self.tests:
            if term and term not in test_id.lower() and term not in desc.lower():
                continue
            status, duration = self.results.get(script, ("pending", ""))
            box = CHECKED if self.selected[script] else UNCHECKED
            self.tree.insert(
                "",
                tk.END,
                iid=script,
                values=(box, test_id, desc, STATUS_TEXT[status], duration),
                tags=(status,),
            )
        self._update_counter()

    def _update_counter(self):
        if not self.tests:
            text = f"No automated tests configured for '{self.module_var.get()}' yet (coming soon)."
        else:
            text = f"Selected {sum(self.selected.values())} / {len(self.tests)}"
            shown = len(self.tree.get_children())
            if shown != len(self.tests):
                text += f"   •   Showing {shown}"
        self.counter_lbl.configure(text=text)

    def _set_checked(self, iid, value):
        self.selected[iid] = value
        self.tree.set(iid, "sel", CHECKED if value else UNCHECKED)

    def _on_tree_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            self._set_checked(iid, not self.selected[iid])
            self._update_counter()
            return "break"

    def _on_tree_space(self, event):
        for iid in self.tree.selection():
            self._set_checked(iid, not self.selected[iid])
        self._update_counter()
        return "break"

    def _set_visible_checked(self, value):
        for iid in self.tree.get_children():
            self._set_checked(iid, value)
        self._update_counter()

    def _select_failed(self):
        for _, script, _, _, _ in self.tests:
            status = self.results.get(script, ("pending", ""))[0]
            self.selected[script] = status == "fail"
        self._refresh_tree()

    def _set_result(
        self, script, status, duration="", duration_sec=0.0, test_id="", module_name=""
    ):
        self.results[script] = (status, duration)
        if self.tree.exists(script):
            self.tree.set(script, "status", STATUS_TEXT[status])
            self.tree.set(script, "time", duration)
            self.tree.item(script, tags=(status,))
            if status == "running":
                self.tree.see(script)

        if status in ("pass", "fail", "stopped") and module_name:
            self.module_results.setdefault(module_name, {})[script] = (
                status,
                duration_sec,
                test_id,
            )
            self.execution_history.append((test_id, duration_sec, status, module_name))
            self._refresh_charts()

    def _on_module_changed(self, event=None):
        self._load_module(self.module_var.get())

    # Small helpers

    def _browse_excel(self):
        current_raw = self.excel_var.get().strip()
        current = Path(current_raw) if current_raw else None
        initial_dir = (
            str(current.parent)
            if current and current.parent.is_dir()
            else str(APP_DIR)
        )
        f = filedialog.askopenfilename(
            title="Select Test Case Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")],
            initialdir=initial_dir,
        )
        if f:
            self.excel_var.set(f)

    def _open_excel(self):
        path = self.excel_var.get().strip()
        if not os.path.isfile(path):
            messagebox.showerror("Excel Missing", f"Could not find:\n{path}")
            return
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Cannot Open", str(e))

    def _clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            initialfile=f"test_log_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            initialdir=str(APP_DIR),
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if path:
            Path(path).write_text(
                self.log_text.get("1.0", tk.END), encoding="utf-8"
            )

    # Thread-safe UI updates (worker thread -> queue -> UI thread)

    def _ui(self, func, *args):
        """Call this from the worker thread to update the UI safely."""
        self.ui_queue.put((func, args))

    def _process_ui_queue(self):
        try:
            for _ in range(300):  # limit per tick so the UI stays responsive
                func, args = self.ui_queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        self.after(100, self._process_ui_queue)

    def _log(self, text):
        self._ui(self._append_log, text)

    def _append_log(self, text):
        self.log_text.insert(tk.END, text + "\n", self._log_tag(text))
        self.log_text.see(tk.END)

    @staticmethod
    def _log_tag(text):
        if "FAIL" in text or ": Fail " in text or "Traceback" in text:
            return "fail"
        if "PASS" in text or ": Pass " in text:
            return "pass"
        if "[!]" in text or "[-]" in text or "STOPPED" in text or "BLOCKED" in text or ": Blocked " in text:
            return "warn"
        if "RUNNING" in text or text.startswith("="):
            return "info"
        return ""

    def _set_status_text(self, text, color="#64748B"):
        self.status_lbl.configure(text=text, foreground=color)

    def _set_progress(self, done, total, passed, failed):
        self.progress_bar["maximum"] = max(total, 1)
        self.progress_bar["value"] = done
        self.summary_lbl.configure(
            text=f"Total: {total}  |  Passed: {passed}  |  Failed: {failed}"
        )

    # Run / Stop

    def _start_run(self):
        if self.is_running:
            return

        selected_tests = [
            (script, tid, desc, home_mod, sheet)
            for tid, script, desc, home_mod, sheet in self.tests
            if self.selected[script]
        ]

        if not selected_tests:
            messagebox.showwarning(
                "No Selection", "Please check at least one test case to execute."
            )
            return

        excel_path = self.excel_var.get().strip()
        if not os.path.isfile(excel_path):
            messagebox.showerror(
                "Excel Missing",
                f"Could not find the Excel file:\n{excel_path}\nPlease browse and select a valid workbook.",
            )
            return

        try:
            with open(excel_path, "ab"):
                pass
        except PermissionError:
            messagebox.showerror(
                "File Locked",
                "The Excel file is currently open in Microsoft Excel.\nPlease save and close it before running tests.",
            )
            return

        selected_mode = self.module_var.get()

        self.is_running = True
        self.stop_requested = False
        self.results.clear()  # reset old statuses for current run
        if selected_mode == "ALL":
            for m in MODULES:
                self.module_results[m] = {}
        else:
            self.module_results[selected_mode] = {}
        self.execution_history.clear()
        self._refresh_tree()
        self._refresh_charts()
        self._set_progress(0, len(selected_tests), 0, 0)
        self._set_status_text("Starting...")

        self.run_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.module_dropdown.configure(state=tk.DISABLED)

        threading.Thread(
            target=self._run_suite_thread,
            args=(selected_tests, excel_path, selected_mode),
            daemon=True,
        ).start()

    def _stop_run(self):
        if not self.is_running:
            return
        self.stop_requested = True
        self.stop_btn.configure(state=tk.DISABLED)
        self._log("\n[!] User requested termination. Stopping...")
        self._kill_current_process()

    def _kill_current_process(self):
        """Kill the running test and its children (Chrome / chromedriver)."""
        proc = self.current_process
        if proc and proc.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=NO_WINDOW,
                    )
                else:
                    proc.terminate()
            except Exception:
                pass

    def _open_allure_report(self):
        import allure_viewer

        if self.allure_server is None:
            self.allure_server = allure_viewer.AllureReportServer()
        server = self.allure_server
        self.allure_btn.configure(state=tk.DISABLED, text="Opening...")

        def _worker():
            try:
                ok, msg = allure_viewer.open_allure_report(APP_DIR, server)
            except Exception as exc:
                self._ui(self._on_allure_done, False, "", str(exc))
                return
            self._ui(self._on_allure_done, ok, msg, "")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_allure_done(self, ok: bool, msg: str, err: str):
        self.allure_btn.configure(state=tk.NORMAL, text="📊 Allure Report")
        if err:
            self._append_log(f"[!] Allure Report error: {err}")
            messagebox.showerror("Allure Report Error", err)
            return
        self._append_log(msg)
        if not ok:
            messagebox.showinfo("Allure Report", msg)

    def _on_close(self):
        if self.is_running:
            if not messagebox.askyesno(
                "Tests Running", "Tests are still running. Stop and exit?"
            ):
                return
            self.stop_requested = True
            self._kill_current_process()
        if self.allure_server is not None:
            try:
                self.allure_server.stop()
            except Exception:
                pass
        self.destroy()

    def _ensure_excel_updated(
        self, excel_path: str, sheet_name: str, test_id: str, desc: str, status: str
    ):
        """Fallback verification: ensures the test result & screenshot link are in the Excel file."""
        try:
            import openpyxl

            wb = openpyxl.load_workbook(excel_path)
            try:
                if sheet_name not in wb.sheetnames:
                    return
                ws = wb[sheet_name]

                # Locate header row & columns
                headers = {}
                h_row_used = 4
                for h_row in (4, 1, 2, 3, 5):
                    for col in range(1, ws.max_column + 1):
                        txt = str(ws.cell(h_row, col).value or "").strip().lower()
                        if txt:
                            headers[col] = txt
                    if any("status" in t or "actual" in t for t in headers.values()):
                        h_row_used = h_row
                        break
                    headers.clear()

                def col_of(*keywords):
                    for kw in keywords:
                        for col, txt in headers.items():
                            if kw in txt:
                                return col
                    return None

                col_actual = col_of("actual")
                col_status = col_of("status")
                col_evidence = col_of("remark", "evidence", "screenshot", "screen shot")
                col_date = col_of("date")
                col_tester = col_of("tester")

                target_row = None
                for r in range(h_row_used + 1, ws.max_row + 1):
                    val = str(ws.cell(r, 1).value or "").strip().lower()
                    if val == test_id.strip().lower():
                        target_row = r
                        break

                if target_row is None:
                    return

                # Find screenshot under SCREENSHOT_DIR (if set), else screenshots/<test_id>/
                shot_roots: list[Path] = []
                env_shot_dir = (os.getenv("SCREENSHOT_DIR") or "").strip()
                if env_shot_dir:
                    raw_shot = Path(env_shot_dir)
                    shot_roots.append(
                        raw_shot if raw_shot.is_absolute() else (APP_DIR / raw_shot).resolve()
                    )
                shot_roots.extend([APP_DIR / "screenshots", BUNDLE_DIR / "screenshots"])

                shot_file = None
                for shot_root in shot_roots:
                    tc_shot_dir = shot_root / test_id.strip()
                    if tc_shot_dir.is_dir():
                        pngs = sorted(
                            tc_shot_dir.glob("*.png"), key=lambda p: p.stat().st_mtime
                        )
                        if pngs:
                            fails = [p for p in pngs if "_FAIL.png" in p.name]
                            shot_file = str((fails[-1] if fails else pngs[-1]).resolve())
                            break

                changed = False
                status_label = "Pass" if status == "pass" else "Fail"

                if col_status and not ws.cell(target_row, col_status).value:
                    ws.cell(target_row, col_status).value = status_label
                    changed = True

                if col_actual and not ws.cell(target_row, col_actual).value:
                    ws.cell(target_row, col_actual).value = (
                        f"{desc} executed ({status_label})"
                    )
                    changed = True

                if col_date and not ws.cell(target_row, col_date).value:
                    ws.cell(target_row, col_date).value = datetime.now().strftime(
                        "%d-%b-%Y"
                    )
                    changed = True

                if col_tester and not ws.cell(target_row, col_tester).value:
                    ws.cell(target_row, col_tester).value = os.getenv(
                        "TESTER_NAME", "Automation"
                    )
                    changed = True

                if col_evidence and shot_file and not ws.cell(target_row, col_evidence).value:
                    cell = ws.cell(target_row, col_evidence)
                    cell.value = os.path.basename(shot_file)
                    cell.hyperlink = shot_file
                    cell.style = "Hyperlink"
                    changed = True

                if changed:
                    wb.save(excel_path)
                    self._log(
                        f"   [Excel Updated]: Row {target_row} in '{sheet_name}' -> {status_label}"
                    )
            finally:
                wb.close()
        except Exception as e:
            self._log(f"   [!] Excel fallback check warning: {e}")

    def _run_suite_thread(self, selected_tests, excel_path, selected_mode):
        resolved_excel = str(Path(excel_path).resolve())
        os.environ["EXCEL_PATH"] = resolved_excel

        total = len(selected_tests)
        passed = 0
        failed = 0
        start_time = time.time()

        self._log("=" * 70)
        self._log(
            f"Starting execution of {total} test(s) for Selection: {selected_mode}"
        )
        self._log(f"Excel Path: {resolved_excel}")
        self._log("=" * 70 + "\n")

        try:
            for idx, (script_name, test_id, desc, home_mod, sheet_name) in enumerate(
                selected_tests, start=1
            ):
                if self.stop_requested:
                    self._log(
                        f"\n[-] Execution aborted by user. {idx - 1}/{total} tests completed."
                    )
                    break

                os.environ["SHEET_NAME"] = sheet_name

                self._ui(
                    self._set_status_text,
                    f"Running [{idx}/{total}]: {test_id} ({desc})...",
                    self.brand_dark,
                )
                self._ui(self._set_result, script_name, "running")
                self._log(
                    f"[{idx}/{total}] RUNNING: {test_id} ({script_name}) [Sheet: {sheet_name}]..."
                )

                script_file = find_script_path(script_name)
                if not script_file:
                    self._log(
                        f"   -> FAIL: Script file '{script_name}' not found in bundle or directory."
                    )
                    failed += 1
                    self._ui(
                        self._set_result,
                        script_name,
                        "fail",
                        "0.0s",
                        0.0,
                        test_id,
                        home_mod,
                    )
                    self._ui(self._set_progress, idx, total, passed, failed)
                    continue

                test_start = time.time()
                status = self._execute_test_process(
                    script_name, script_file, sheet_name, resolved_excel
                )
                elapsed = time.time() - test_start
                duration = f"{elapsed:.1f}s"

                if status == "pass":
                    passed += 1
                    self._log(f"   -> PASS ({duration})\n")
                elif status == "stopped":
                    self._log(f"   -> STOPPED ({duration})\n")
                else:
                    failed += 1
                    self._log(f"   -> FAIL ({duration})\n")

                if status in ("pass", "fail"):
                    self._ensure_excel_updated(
                        resolved_excel, sheet_name, test_id, desc, status
                    )

                self._ui(
                    self._set_result,
                    script_name,
                    status,
                    duration,
                    elapsed,
                    test_id,
                    home_mod,
                )
                self._ui(self._set_progress, idx, total, passed, failed)
        finally:
            self._log("=" * 70)
            self._log(f"COMPLETED in {time.time() - start_time:.1f}s")
            self._log(
                f"Summary: Total: {total} | Passed: {passed} | Failed: {failed}"
            )
            self._log("=" * 70)
            self._ui(self._finish_run, passed, failed)

    def _finish_run(self, passed, failed):
        if self.stop_requested:
            self._set_status_text(
                f"Stopped by user. Passed: {passed}, Failed: {failed}", "#D97706"
            )
        elif failed:
            self._set_status_text(
                f"Finished with failures. Passed: {passed}, Failed: {failed}",
                "#DC2626",
            )
        else:
            self._set_status_text(
                f"Finished! All {passed} test(s) passed.", "#059669"
            )

        self.run_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.module_dropdown.configure(state="readonly")
        self.is_running = False
        self._refresh_charts()

    def _execute_test_process(
        self,
        rel_script_name: str,
        script_path: Path,
        sheet_name: str,
        excel_path: str,
    ):
        """Runs one test file. Returns 'pass', 'fail' or 'stopped'."""
        import allure_viewer

        allure_dir = str(allure_viewer.resolve_allure_results_dir(APP_DIR))
        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
            "SHEET_NAME": sheet_name,
            "EXCEL_PATH": excel_path,
            "DMS_ALLURE_RESULTS_DIR": allure_dir,
            "REPORT_ALLURE_RESULTS_DIR": allure_dir,
        }

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--worker-test", rel_script_name, sheet_name]
        else:
            cmd = [sys.executable, str(script_path)]
            if script_path.name == "main.py":
                cmd.append("all")

        # Run inside script's parent folder (e.g., core/) so relative imports & .env work
        work_dir = (
            str(script_path.parent)
            if script_path.parent.exists()
            else str(APP_DIR)
        )

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=work_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=NO_WINDOW,
            )
            self.current_process = proc

            saw_failure = False
            if proc.stdout is not None:
                for line in proc.stdout:
                    clean_line = line.rstrip()
                    if clean_line:
                        self._log(f"   {clean_line}")
                        if (
                            clean_line.startswith("FAILED :")
                            or clean_line.startswith("Something went wrong:")
                            or clean_line.startswith("Suite crashed:")
                            or clean_line.startswith("Run aborted:")
                        ):
                            saw_failure = True

            proc.wait()
            if self.stop_requested:
                return "stopped"
            if proc.returncode == 0 and not saw_failure:
                return "pass"
            return "fail"
        except Exception as e:
            self._log(f"   Exception during execution: {e}")
            return "fail"
        finally:
            self.current_process = None


if __name__ == "__main__":
    run_as_worker()
    app = AutomationRunnerGUI()
    app.mainloop()