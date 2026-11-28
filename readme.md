# Robo2mation Selenium Test Automation Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green.svg)](https://www.selenium.dev/)
[![Pattern](https://img.shields.io/badge/Pattern-Page%20Object%20Model-orange.svg)](#architecture-how-a-test-works)
[![Reporting](https://img.shields.io/badge/Reporting-Allure%202%20%26%20Excel-informational.svg)](#engineering-highlights)
[![Runner](https://img.shields.io/badge/Runner-CLI%20%26%20Tkinter%20GUI-lightgrey.svg)](#running-tests-viewing-reports-and-packaging)

An end-to-end Python and Selenium 4 test automation suite for the **Robo2mation Enterprise Content Management (ECM)** platform. The repository contains **212 automated test scripts** across four functional suites (**DMS**, **Report**, **Configurable**, and **Login**), backed by Page Object Model abstractions, process-isolated CLI batch runners, a High-DPI Windows Tkinter desktop runner, Allure 2 reporting with a built-in HTML viewer, and automated Excel sanity-tracker updates.

---

## Table of Contents

- [Engineering Highlights](#engineering-highlights)
- [Repository Structure](#repository-structure)
- [Architecture: How a Test Works](#architecture-how-a-test-works)
- [Test Suites Overview (212 Automated Tests)](#test-suites-overview-212-automated-tests)
- [Tech Stack & Dependencies](#tech-stack--dependencies)
- [Setup & Configuration](#setup--configuration)
- [Running Tests, Viewing Reports, and Packaging](#running-tests-viewing-reports-and-packaging)
- [Troubleshooting](#troubleshooting)
- [Authors & Maintainers](#authors--maintainers)

---

## Engineering Highlights

| Capability | Implementation Details | Key Files |
|---|---|---|
| **Page Object Model & Session Facades** | DOM locators and `WebDriverWait` synchronization are encapsulated inside dedicated `pages/` classes; tests execute through high-level session facades (`DmsSession`, `ReportSession`, `ConfigurableSession`). | [dms/pages/](robo2_test_cases/dms/pages/), [dms/common.py](robo2_test_cases/dms/common.py), [report/common.py](robo2_test_cases/dms/report/common.py), [configurable/common.py](robo2_test_cases/dms/configurable/common.py) |
| **Role-Based & Maker-Checker Testing** | Multi-account session switching (`as_other_user`, `login_as_role`) verifies segregation of duties across document review workflows, user approval/rejection lifecycles, and role-scoped report visibility (`own`, `all`, department/process, `denied`). | [dms/env_config.py](robo2_test_cases/dms/env_config.py), `tc127`–`tc131`, `con001`–`con024`, `rep001`–`rep102` |
| **Process-Isolated Execution** | Batch runners execute each script in a dedicated OS subprocess (`subprocess.run` / `subprocess.Popen`) with a 10-minute per-test timeout, so one browser crash or hang cannot abort remaining tests. Exit codes distinguish `PASS` (`0`), `FAIL` (`1`), and `BLOCKED` (`2`). | [dms/run_all.py](robo2_test_cases/dms/run_all.py), [report/run_all.py](robo2_test_cases/dms/report/run_all.py) |
| **Dual Reporting (Allure 2 + Excel)** | Generates step-level Allure 2 JSON results with screenshots, failure DOM HTML, and Python tracebacks, while `openpyxl` writes `Pass`/`Fail`/`Blocked` status, actual result text, tester name, date, and screenshot hyperlinks directly into the `.xlsx` workbook. | [dms/allure_reporter.py](robo2_test_cases/dms/allure_reporter.py), [dms/allure_viewer.py](robo2_test_cases/dms/allure_viewer.py), [dms/common.py](robo2_test_cases/dms/common.py) |
| **Pre-Flight Checks & Self-Cleanup** | Validates required `.env` settings and checks that the Excel workbook exists and is unlocked before launching Chrome; `finally` hooks clean up temporary categories, master-table methods, and watermarks and always close WebDriver via `driver.quit()`. | [dms/common.py](robo2_test_cases/dms/common.py) |
| **Desktop GUI & Standalone Packaging** | High-DPI Windows Tkinter client featuring module/test selection, live threaded console output (`queue.Queue`), custom Canvas summary/timing charts, a one-click localhost Allure report viewer, and PyInstaller `.exe` packaging. | [dms/app_gui.py](robo2_test_cases/dms/app_gui.py), [dms/build_exe.py](robo2_test_cases/dms/build_exe.py), [dms/build_exe.bat](robo2_test_cases/dms/build_exe.bat) |

---

## Repository Structure

```text
Selenium/
├── .gitignore                                     # Excludes .env files, logs, screenshots, downloads, builds, and .xlsx trackers
├── readme.md                                      # Project documentation
└── robo2_test_cases/
    ├── .env.example                               # Environment template for the Core Login suite
    ├── Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx # Local Excel test tracker (git-ignored)
    │
    ├── login/                                     # Core Login Sanity Suite (2 tests)
    │   ├── common.py                              # Shared login, screenshot, and Excel summary updater
    │   ├── login_valid.py                         # COR-TC001: Valid credentials redirect
    │   └── login_invalid.py                       # COR-TC002: Invalid credentials error alert
    │
    └── dms/                                       # Robo2mation ECM Automation Framework
        ├── app_gui.py                             # High-DPI Tkinter Desktop Test Runner & Analytics UI
        ├── run_all.py                             # Process-isolated CLI batch runner for DMS tests
        ├── build_exe.py                           # PyInstaller build script for Windows standalone app
        ├── build_exe.bat                          # Windows batch wrapper for build_exe.py
        ├── env_config.py                          # Shared env/path/credential loader across DMS, Report, and Configurable
        ├── dms_config.py                          # DMS routes, directories, and configuration validation
        ├── common.py                              # DmsSession facade, browser factory, Allure & Excel reporting
        ├── allure_reporter.py                     # Allure 2 lifecycle wrapper (steps, screenshots, DOM, tracebacks)
        ├── allure_viewer.py                       # Built-in offline HTML report generator & localhost HTTP viewer
        ├── .env.example                           # Shared environment template (DMS, Report, Configurable)
        ├── pages/                                 # DMS Page Objects (9 modules)
        │   ├── base_page.py                       # Base waits, popup/alert helpers, shared navigation
        │   ├── login_page.py                      # Authentication & multi-user switching
        │   ├── upload_page.py                     # Standard upload, metadata, naming, watermarks
        │   ├── document_view_page.py              # Versions, checkout, archive/delete, sharing, OCR, Ask Effy
        │   ├── explorer_page.py                   # My Documents tree, grid/list views, sorting, search
        │   ├── categorization_page.py             # Categories, doc-types, access/owner groups, metadata schemas
        │   ├── bulk_upload_page.py                # Bulk Excel template download/upload & validation
        │   ├── master_table_page.py               # Master table method CRUD, filtering, cloning, assignment
        │   └── review_page.py                     # Maker-Checker pending review queue & approve/reject actions
        ├── tc002_*.py .. tc139_*.py               # 85 automated DMS test scripts
        │
        ├── report/                                # Report Suite (101 tests)
        │   ├── run_all.py                         # Process-isolated CLI batch runner for Report tests
        │   ├── common.py                          # ReportSession facade & run_report_test() runner
        │   ├── report_config.py                   # Report routes, role profiles, and selector config
        │   ├── report_data.py                     # Data-driven filter datasets, expected texts, rolling date ranges
        │   ├── allure_reporter.py                 # Report suite Allure 2 adapter
        │   ├── pages/                             # Report Page Objects (4 modules)
        │   │   ├── base_page.py
        │   │   ├── login_page.py
        │   │   ├── report_page.py
        │   │   └── requested_downloads_page.py
        │   └── rep001_*.py .. rep102_*.py         # 101 automated Report test scripts
        │
        ├── configurable/                          # User Governance Suite (24 tests)
        │   ├── common.py                          # ConfigurableSession facade, standalone Allure writer & Excel updater
        │   ├── configurable_config.py             # Configurable role profiles, routes, and env overrides
        │   ├── pages/                             # Configurable Page Objects (2 modules)
        │   │   ├── login_page.py
        │   │   └── user_management_page.py
        │   └── con001_*.py .. con024_*.py         # 24 automated Configurable test scripts
        │
        ├── test_files/                            # Sample upload files for 18 extensions (git-ignored)
        ├── screenshots/                           # Captured pass/fail screenshots (git-ignored)
        ├── downloads/                             # Browser downloads verified by tests (git-ignored)
        ├── logs/                                  # Non-passing subprocess logs from run_all.py (git-ignored)
        ├── allure-results/                        # Raw Allure 2 JSON & attachments (git-ignored)
        ├── assets/                                # GUI icons and scaled logos (git-ignored)
        └── build/ , dist/                         # PyInstaller build artifacts (git-ignored)
```

---

## Architecture: How a Test Works

Every test in the DMS, Report, and Configurable suites follows a four-layer pipeline:

1. **Configuration (`env_config.py` + suite `*_config.py`)** — Resolves settings with clear precedence: OS or GUI environment variables take priority, followed by optional suite-local overrides (`.env.report` / `.env.configurable`), falling back to the shared `robo2_test_cases/dms/.env`.
2. **Page Objects (`pages/`)** — Encapsulate Selenium `WebDriverWait` conditions, resilient selectors, and UI interactions so locator changes stay isolated to one class.
3. **Session Facade (`DmsSession`, `ReportSession`, `ConfigurableSession`)** — Exposes domain actions (`login_as_role`, `new_document`, `verify_scope`, `step`) so individual test scripts stay short and declarative.
4. **Unified Test Runner (`run_dms_test`, `run_report_test`, `run_configurable_test`)** — Validates `.env` prerequisites and Excel workbook access before starting Chrome, creates Allure steps and screenshot attachments, executes cleanup in `finally`, calls `driver.quit()`, and writes the outcome back to the Excel tracker.

For example, [rep001_core_login_report.py](robo2_test_cases/dms/report/rep001_core_login_report.py) expresses an entire role-visibility check in a single function:

```python
import common as c

TEST_CASE_ID = "REP-TC001"
ROUTE = "/report/login_report/"

def test_own_login_report(session: c.ReportSession) -> str:
    session.login_as_role("core_user")
    session.open_report(ROUTE)
    return session.verify_scope("own")

if __name__ == "__main__":
    c.run_report_test(TEST_CASE_ID, ROUTE, test_own_login_report, __doc__)
```

---

## Test Suites Overview (212 Automated Tests)

### 1. DMS Suite (`robo2_test_cases/dms/` — 85 Tests, `DMS-TC002` to `DMS-TC139`)

| Functional Area | Test Scripts | Scope & Validations |
|---|---|---|
| **Multi-Format Attachments** | `tc002` | Uploads and validates 18 extensions (`pdf`, `png`, `jpg`, `jpeg`, `svg`, `gif`, `mp3`, `mp4`, `doc`, `docx`, `xls`, `xlsx`, `csv`, `ppt`, `pptx`, `msg`, `eml`, `txt`). |
| **Upload, Naming & Viewer** | `tc003`, `tc009`, `tc012`, `tc024`, `tc055`, `tc056` | Required metadata upload, document naming conventions, grid/list views, and full-screen document viewing in new tabs. |
| **Downloads & PDF Merging** | `tc011`, `tc022`, `tc023` | Multi-PDF merge into a single asset, single document download, and multi-document `.zip` batch download. |
| **Versioning & Concurrency** | `tc014`–`tc016`, `tc020`, `tc021` | Uploading new file versions with extended names, downloading/deleting revisions, check-out locking, and cancelling check-out. |
| **Lifecycle, Trash & Related Files** | `tc025`–`tc028`, `tc030`, `tc031` | Archiving and restoring documents, soft-deletion and recovery from trash, and linking/unlinking related files. |
| **Sharing & Watermarking** | `tc032`–`tc034`, `tc036`, `tc042`, `tc045`, `tc046`, `tc049`, `tc050` | Sharing with users/groups/all, external public links, email sharing, revoking shares, custom text/image watermarks, search, attach, and delete. |
| **Explorer & Sorting** | `tc051`, `tc057`–`tc062` | My Documents permission checks, default sorting, name/date ascending/descending sorting, and category/doc-type sorting. |
| **Categorization & Governance** | `tc067`, `tc069`, `tc073`, `tc075`–`tc078`, `tc080`–`tc084` | Category/doc-type CRUD, deleted category map/full-path/restore/purge, publishing doc-types, access/owner group assignment, and notifications. |
| **Metadata & Uniqueness Rules** | `tc019`, `tc085`–`tc087`, `tc090`–`tc092` | Dynamic metadata schema CRUD, editing document metadata, and single, `OR`, and `AND` metadata uniqueness enforcement. |
| **Bulk Upload & Master Tables** | `tc093`–`tc095`, `tc132`, `tc101`–`tc110`, `tc112` | Bulk template download, invalid/valid template validation, large bulk ingest, and master table method CRUD, filter, search, toggle, clone, and assign. |
| **Search & Saved Queries** | `tc119`, `tc121`, `tc122`, `tc124`–`tc126` | Quick search, advanced search (`Match All` on/off, include archived), saving searches, and listing saved queries. |
| **Maker-Checker, OCR & AI** | `tc127`, `tc128`, `tc130`, `tc131`, `tc037`, `tc136`, `tc137`, `tc139` | Multi-user Maker-Checker review queue and approve/reject flow, OCR indexing in advanced/explorer search, and "Chat With PDF" (Ask Effy AI). |

### 2. Report Suite (`robo2_test_cases/dms/report/` — 101 Tests, `REP-TC001` to `REP-TC102`, excluding `REP-TC046`)

Uses data-driven filter datasets and rolling 30-day date windows from [report_data.py](robo2_test_cases/dms/report/report_data.py) to validate role visibility (`own`, `all`, department/process scopes, `denied`), multi-field search, date-range filtering, column sorting, and direct or queued exports across 16 reports:

| Report Category | Test Scripts | Covered Reports |
|---|---|---|
| **Core Reports** | `rep001`–`rep017` | Core Login (`rep001`–`rep005`), Core Activity (`rep006`–`rep012`), Core API (`rep013`–`rep017`) |
| **DMS Reports** | `rep018`–`rep045`, `rep047`–`rep054` | DMS Activity (`rep018`–`rep023`), Document Summary (`rep024`), Upload Record (`rep025`–`rep030`), Document Record (`rep031`–`rep036`), Archived Document Record (`rep037`–`rep042`), Document Type Accessibility (`rep043`–`rep045`, `rep047`–`rep048`), Page Count (`rep049`–`rep054`) |
| **Workflow & Analytics** | `rep055`–`rep102` | KPI (`rep055`–`rep063`, direct `< 100` vs. queued `> 100` exports), Task Activity (`rep064`–`rep071`), Application Activity (`rep072`–`rep078`), Workflow Activity (`rep079`–`rep086`), Custom Report (`rep087`–`rep094`), Auto Approval (`rep095`–`rep102`) |

### 3. Configurable User Governance Suite (`robo2_test_cases/dms/configurable/` — 24 Tests, `CON-TC001` to `CON-TC024`)

| Coverage Area | Test Scripts | Scope & Validations |
|---|---|---|
| **Admin & Maker Workflows** | `con001`–`con009` | Admin role route access, User Maker panel visibility, creating approval requests, updating requests before/after approval, and Users/Approval table controls & row options. |
| **Checker Workflows** | `con010`–`con016` | User Checker panel visibility, approving/rejecting requests before and after updates, mandatory/optional reject comments, and Users/Approval table controls & row options. |
| **Account Lifecycle & Lockout** | `con017`–`con024` | Inactive and blocked user login restrictions, rejected user login denial and username reuse, pending/approved/rejected update request effects, dual Maker & Checker permissions, and 5-attempt failed login lockout. |

### 4. Core Login Sanity Suite (`robo2_test_cases/login/` — 2 Tests, `COR-TC001` to `COR-TC002`)

| Test ID | Script | Scenario & Verification |
|---|---|---|
| `COR-TC001` | [login_valid.py](robo2_test_cases/login/login_valid.py) | Logs in with valid credentials and verifies the password field disappears upon dashboard redirect. |
| `COR-TC002` | [login_invalid.py](robo2_test_cases/login/login_invalid.py) | Submits invalid credentials and verifies an error banner/toast is displayed. |

Both scripts update row status, actual result, evidence screenshot path, date, tester, and summary counters (`D2`, `F2`, `H2`) via [login/common.py](robo2_test_cases/login/common.py).

---

## Tech Stack & Dependencies

| Tool / Library | Purpose |
|---|---|
| **Python 3.10+** | Core runtime (uses PEP 604 `X \| Y` union syntax and `pathlib`) |
| **Selenium WebDriver 4.x** | Browser automation, explicit waits (`WebDriverWait`), and automatic driver resolution via Selenium Manager |
| **openpyxl** | Reading and updating `.xlsx` sanity test sheets with pass/fail status and screenshot hyperlinks |
| **python-dotenv** | Loading environment variables from `.env` and suite-local override files |
| **allure-python-commons** | Recording Allure 2 test cases, nested steps, screenshots, DOM snapshots, and tracebacks |
| **Tkinter** *(stdlib)* | Desktop GUI runner (`app_gui.py`) with live log streaming and Canvas analytics charts |
| **PyInstaller** *(optional)* | Packaging `app_gui.py` and test suites into a standalone Windows directory/executable |

---

## Setup & Configuration

### 1. Prerequisites

- **OS**: Windows 10/11 recommended (required for High-DPI Tkinter scaling and PyInstaller `.exe` builds; CLI scripts run wherever Python 3.10+ and Google Chrome are available).
- **Python**: 3.10 or higher.
- **Browser**: Google Chrome installed (Selenium Manager resolves ChromeDriver automatically).
- **Target & Tracker**: Access to a Robo2mation ECM v6 environment and the local `.xlsx` test tracker workbook (`Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx`).

### 2. Clone and Install Dependencies

```powershell
git clone https://github.com/ays19/Selenium.git
cd Selenium

python -m venv .venv
.venv\Scripts\activate

pip install selenium openpyxl python-dotenv allure-python-commons
```

If you also plan to build the standalone Windows executable, install PyInstaller:

```powershell
pip install pyinstaller
```

### 3. Configure Environment Files

1. **DMS, Report, and Configurable suites** — Copy [robo2_test_cases/dms/.env.example](robo2_test_cases/dms/.env.example) to `robo2_test_cases/dms/.env` and populate at minimum `BASE_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `GENERAL_USERNAME`, `GENERAL_PASSWORD`, `EXCEL_PATH`, and `TESTER_NAME` (plus suite-specific fields like `OTHER_USERNAME`/`OTHER_PASSWORD`, `DOC_TYPE`, or optional `.env.report` / `.env.configurable` overrides).
2. **DMS upload sample files** — Place sample test files inside `robo2_test_cases/dms/test_files/`. (`tc002_document_attach.py` checks for all 18 extensions: `pdf`, `png`, `jpg`, `jpeg`, `svg`, `gif`, `mp3`, `mp4`, `doc`, `docx`, `xls`, `xlsx`, `csv`, `ppt`, `pptx`, `msg`, `eml`, `txt`.)
3. **Core Login suite** — Copy [robo2_test_cases/.env.example](robo2_test_cases/.env.example) to `robo2_test_cases/login/.env` (or `robo2_test_cases/.env`) and set `SITE_URL`, `VALID_USER`, `VALID_PASS`, `EXCEL_FILE`, and `TESTER_NAME`.

---

## Running Tests, Viewing Reports, and Packaging

> **Note:** Keep the target `.xlsx` workbook closed in Microsoft Excel while running tests so `openpyxl` can save results without file-lock errors.

### DMS CLI Batch Runner

```powershell
cd robo2_test_cases/dms

# Run all 85 DMS tests sequentially in isolated processes
python run_all.py

# Run specific tests by filename prefix
python run_all.py tc014 tc022

# Run a single test directly
python tc014_version_doc_upload.py
```

### Report CLI Batch Runner

```powershell
cd robo2_test_cases/dms/report

# Run all 101 Report tests sequentially
python run_all.py

# Run specific report tests by prefix
python run_all.py rep001 rep024

# Run a single report test
python rep001_core_login_report.py
```

### Configurable & Login Suites

```powershell
# Configurable suite (single test, or iterate all con*.py scripts)
cd robo2_test_cases/dms/configurable
python con001_admin_user_approval_requests.py
Get-ChildItem con*.py | ForEach-Object { python $_.Name }

# Core Login suite
cd robo2_test_cases/login
python login_valid.py
python login_invalid.py
```

### Desktop GUI Runner

```powershell
cd robo2_test_cases/dms
python app_gui.py
```

- Select a module (`DMS`, `Report`, `ALL`, or `Core` if a local `core/` module is present), verify the **Test Case Excel** path, and check the tests to run.
- Click **Run Tests** to monitor live logs in **Console Log** and pass/fail/timing charts in **Charts & Analytics**.
- Click **Allure Report** to inspect step-level results in your browser. If the Allure CLI is installed, it generates the official report; otherwise [allure_viewer.py](robo2_test_cases/dms/allure_viewer.py) builds an offline HTML report and serves it over a local HTTP server automatically.

If you prefer the Allure CLI from a terminal:

```powershell
cd robo2_test_cases/dms
allure serve allure-results
```

### Building the Standalone Windows Executable

```powershell
cd robo2_test_cases/dms

# Option A: batch script (auto-detects .venv)
build_exe.bat

# Option B: direct Python execution
python build_exe.py
```

The packaged application is written to `robo2_test_cases/dms/dist/Robo2mation_Runner/Robo2mation_Runner.exe`.

---

## Troubleshooting

- **Excel file locked (`PermissionError` / `"Close the Excel file first, then run again."`)** — Close `Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx` in Microsoft Excel before starting a CLI or GUI run.
- **`BLOCKED` status (exit code `2`)** — A pre-flight check detected missing credentials, role profiles, or feature-specific `.env` keys (such as `OTHER_USERNAME`, `OCR_DOC_TYPE`, or `LOCK_TARGET_USERNAME`). Review the console output or `logs/<test>.log` and populate the required variable in `robo2_test_cases/dms/.env`.
- **Missing upload samples in `test_files/`** — Ensure `robo2_test_cases/dms/test_files/` contains sample files for every extension required by `tc002_document_attach.py`.
- **`EXCEL_FILE` not found in `robo2_test_cases/login/`** — Paths in `.env` are resolved relative to the current working directory. When launching from `robo2_test_cases/login/`, set `EXCEL_FILE=../Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx` or use an absolute path.
- **Running headless in background/batch runs** — Set `HEADLESS=true` in `robo2_test_cases/dms/.env` (or suite-specific `DMS_HEADLESS=true`, `REPORT_HEADLESS=true`, `CONFIGURABLE_HEADLESS=true`).

---

## Authors & Maintainers

- **Repositories & Profiles**: [github.com/ays19/Selenium](https://github.com/ays19/Selenium), [github.com/AtiqurRahman25](https://github.com/AtiqurRahman25)
- **Focus**: QA Automation, Selenium WebDriver, Test Reporting & Desktop Runner Tooling.
