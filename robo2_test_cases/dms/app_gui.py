"""
Robo2mation Test Automation Suite Desktop Client
Supports Module Selection (DMS, Core, Workflow, Reports),
High-DPI crystal-clear display, Live Execution Charts, and standalone PyInstaller compilation.
"""

import importlib
import math
import os
from pathlib import Path
import queue
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

# Ensure both BUNDLE_DIR (_internal) and APP_DIR are searchable by Python
for p in [str(BUNDLE_DIR), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def find_script_path(script_name: str) -> Path | None:
    """Finds a test script whether inside _internal or alongside the exe."""
    for base in [BUNDLE_DIR, APP_DIR]:
        candidate = base / script_name
        if candidate.exists():
            return candidate
    return None


# SUBPROCESS WORKER DISPATCHER

def run_as_worker():
    """Runs a single test case file in process isolation when called with CLI args."""
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker-test":
        test_module_name = sys.argv[2]
        sheet_name = sys.argv[3] if len(sys.argv) > 3 else "DMS"
        os.environ["SHEET_NAME"] = sheet_name

        try:
            mod_stem = Path(test_module_name).stem
            mod = importlib.import_module(mod_stem)
            if hasattr(mod, "main"):
                mod.main()
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
                "DMS-TC0101",
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
        "tests": [],
    },
    "Workflow": {
        "sheet_name": "Workflow",
        "tests": [],
    },
    "Report": {
        "sheet_name": "Report",
        "tests": [],
    },
    "Configurable": {
        "sheet_name": "Configurable",
        "tests": [],
    },
}


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

        # Data for the selected module and cross-module tracking for charts
        self.tests = []  # [(test_id, script_name, description)]
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

        # Module dropdown
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
            values=list(MODULES.keys()),
            state="readonly",
            width=14,
            font=("Segoe UI", 9),
        )
        self.module_dropdown.grid(
            row=0, column=1, sticky=tk.W, padx=(0, 24), pady=4
        )
        self.module_dropdown.bind("<<ComboboxSelected>>", self._on_module_changed)

        # Excel file
        ttk.Label(
            bar,
            text="Test Case Excel:",
            font=("Segoe UI", 9, "bold"),
            background=self.card_bg,
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 6), pady=4)
        default_excel = os.getenv(
            "EXCEL_PATH",
            str(APP_DIR / "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"),
        )
        self.excel_var = tk.StringVar(value=default_excel)
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
            ("Configurable", "Configurable"),
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

        # Aggregate counts from current module (or all modules if current is empty)
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
            short_id = tid.replace("DMS-", "")
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

    # Test list handling

    def _load_module(self, module_name):
        self.tests = MODULES.get(module_name, {}).get("tests", [])
        self.selected = {script: True for _, script, _ in self.tests}
        # Restore any previous results for this module
        saved = self.module_results.get(module_name, {})
        self.results = {
            script: (st, f"{dur:.1f}s" if dur > 0 else "")
            for script, (st, dur, _) in saved.items()
        }
        self.search_var.set("")
        self._refresh_tree()
        self._refresh_charts()

    def _refresh_tree(self):
        """Rebuild the table, applying the search filter."""
        self.tree.delete(*self.tree.get_children())
        term = self.search_var.get().strip().lower()

        for test_id, script, desc in self.tests:
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
        for _, script, _ in self.tests:
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
        f = filedialog.askopenfilename(
            title="Select Test Case Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")],
            initialdir=str(APP_DIR),
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
        if "FAIL" in text or "Traceback" in text:
            return "fail"
        if "PASS" in text:
            return "pass"
        if "[!]" in text or "[-]" in text or "STOPPED" in text:
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
            (script, tid, desc)
            for tid, script, desc in self.tests
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

        module_name = self.module_var.get()
        sheet_name = MODULES[module_name]["sheet_name"]

        self.is_running = True
        self.stop_requested = False
        self.results.clear()  # reset old statuses for current run
        self.module_results[module_name] = {}
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
            args=(selected_tests, excel_path, module_name, sheet_name),
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

    def _on_close(self):
        if self.is_running:
            if not messagebox.askyesno(
                "Tests Running", "Tests are still running. Stop and exit?"
            ):
                return
            self.stop_requested = True
            self._kill_current_process()
        self.destroy()

    def _run_suite_thread(self, selected_tests, excel_path, module_name, sheet_name):
        os.environ["EXCEL_PATH"] = str(Path(excel_path).resolve())
        os.environ["SHEET_NAME"] = sheet_name

        total = len(selected_tests)
        passed = 0
        failed = 0
        start_time = time.time()

        self._log("=" * 70)
        self._log(
            f"Starting execution of {total} test(s) for Module: {module_name} (Sheet: {sheet_name})"
        )
        self._log(f"Excel Path: {excel_path}")
        self._log("=" * 70 + "\n")

        try:
            for idx, (script_name, test_id, desc) in enumerate(
                selected_tests, start=1
            ):
                if self.stop_requested:
                    self._log(
                        f"\n[-] Execution aborted by user. {idx - 1}/{total} tests completed."
                    )
                    break

                self._ui(
                    self._set_status_text,
                    f"Running [{idx}/{total}]: {test_id} ({desc})...",
                    self.brand_dark,
                )
                self._ui(self._set_result, script_name, "running")
                self._log(f"[{idx}/{total}] RUNNING: {test_id} ({script_name})...")

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
                        module_name,
                    )
                    self._ui(self._set_progress, idx, total, passed, failed)
                    continue

                test_start = time.time()
                status = self._execute_test_process(script_file, sheet_name)
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

                self._ui(
                    self._set_result,
                    script_name,
                    status,
                    duration,
                    elapsed,
                    test_id,
                    module_name,
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

    def _execute_test_process(self, script_path: Path, sheet_name: str):
        """Runs one test file. Returns 'pass', 'fail' or 'stopped'."""
        env = {
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "SHEET_NAME": sheet_name,
        }

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--worker-test", script_path.name, sheet_name]
        else:
            cmd = [sys.executable, str(script_path)]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(APP_DIR),
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

            for line in proc.stdout:
                clean_line = line.rstrip()
                if clean_line:
                    self._log(f"   {clean_line}")

            proc.wait()
            if proc.returncode == 0:
                return "pass"
            return "stopped" if self.stop_requested else "fail"
        except Exception as e:
            self._log(f"   Exception during execution: {e}")
            return "fail"
        finally:
            self.current_process = None


if __name__ == "__main__":
    run_as_worker()
    app = AutomationRunnerGUI()
    app.mainloop()