# Enterprise Selenium Test Automation & QA Engineering Suite

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green.svg)](https://www.selenium.dev/)
[![Framework](https://img.shields.io/badge/Architecture-Process--Isolated%20Runner%20%7C%20Tkinter%20GUI-orange.svg)]()
[![Reporting](https://img.shields.io/badge/Reporting-Excel%20Tracker%20%7C%20Screenshots%20%7C%20Logs-informational.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Chrome-lightgrey.svg)]()

An enterprise-grade test automation and QA engineering portfolio demonstrating real-world software testing practices, test architecture design, and automation tooling. The repository spans end-to-end (E2E) browser automation, an **85 test-case sanity suite** for an Enterprise Content Management (ECM) system (87 automated tests across the repo), two-way automated Excel test tracking, process-isolated batch execution, a standalone Windows desktop GUI runner, and web scraping with structured data pipelines.

---

## 📋 Table of Contents
- [Executive Overview](#executive-overview)
- [Recruiter Competencies & Skills Matrix](#recruiter-competencies--skills-matrix)
- [Repository Architecture](#repository-architecture)
- [Core Projects](#core-projects)
  - [1. Robo2mation DMS Enterprise Test Suite (85 Tests)](#1-robo2mation-dms-enterprise-test-suite-85-tests)
  - [2. Desktop GUI Test Runner & Executable Packaging](#2-desktop-gui-test-runner--executable-packaging)
  - [3. Core Authentication Sanity Suite & Excel Tracker](#3-core-authentication-sanity-suite--excel-tracker)
  - [4. Web Scraping & E2E Extraction Automation](#4-web-scraping--e2e-extraction-automation)
- [Tech Stack & Dependencies](#tech-stack--dependencies)
- [Prerequisites & Environment Setup](#prerequisites--environment-setup)
- [Step-by-Step Execution Guide](#step-by-step-execution-guide)
  - [Quick Start: SauceDemo Automation (No Credentials Required)](#quick-start-saucedemo-automation-no-credentials-required)
  - [Running the Core Login Tests](#running-the-core-login-tests)
  - [Running the DMS Suite via CLI Batch Runner](#running-the-dms-suite-via-cli-batch-runner)
  - [Launching the Desktop GUI Runner](#launching-the-desktop-gui-runner)
  - [Compiling Standalone Executable (PyInstaller)](#compiling-standalone-executable-pyinstaller)
- [QA Engineering Patterns & Best Practices](#qa-engineering-patterns--best-practices)
- [Troubleshooting & FAQ](#troubleshooting--faq)

---

## 🌟 Executive Overview

This repository demonstrates how modern QA automation bridges the gap between engineering rigor and business reporting:

1. **Enterprise Test Automation (Robo2mation ECM)**: A comprehensive test suite featuring 85 automated test scenarios for a Document Management System. Tests cover multi-format uploads (18 extensions), document versioning, check-out/check-in locks, Maker-Checker review approval workflows, Optical Character Recognition (OCR), metadata uniqueness rules, and GenAI-powered features ("Chat with PDF").
2. **Process-Isolated Test Execution**: A custom batch runner (`run_all.py`) that executes tests in dedicated OS subprocesses. A crash, browser timeout, or unhandled exception in one test cannot compromise the execution of subsequent tests.
3. **No-Code / Non-Technical Desktop Tooling**: An enterprise Tkinter desktop client (`app_gui.py`) with Windows Per-Monitor High-DPI scaling, interactive test selection, live charts, and real-time execution logs. Packaged via PyInstaller into a standalone `.exe` so manual testers and stakeholders can run automation suites without Python or Git.
4. **Automated Two-Way Excel Audit Trail**: Tests automatically read expected test cases and write execution status (`Pass`/`Fail`), failure diagnostic reasons, timestamped screenshot hyperlinks, tester name, and execution date back into `Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx`, dynamically recalculating KPI summary cells.
5. **Production Scraping & Data Pipeline**: A self-contained SauceDemo scraper showcasing headless browser navigation, explicit DOM synchronization, multi-handler logging, and simultaneous CSV/JSON data extraction.

---

## 🎯 Recruiter Competencies & Skills Matrix

| Competency / Domain | Implementation Details | Repository Artifacts |
|---|---|---|
| **Selenium WebDriver Core** | Explicit waits (`WebDriverWait`), expected conditions (`EC`), dynamic XPath/CSS locators, action chains, window management. | `dms/common.py`, `login/common.py`, `scraper.py` |
| **Enterprise Workflow Testing** | Multi-user Maker-Checker approval flows, permission boundaries, checkout locks, and document lifecycles (trash, restore, archive). | `tc127_document_maker_checker_feature.py`, `tc130_document_review_by_checker.py`, `tc131_document_approve_reject.py` |
| **Multi-Format Ingestion** | Robust file attachment automation across 18 MIME types (`pdf`, `png`, `jpg`, `svg`, `gif`, `mp3`, `mp4`, `doc`, `docx`, `xls`, `xlsx`, `csv`, `ppt`, `pptx`, `msg`, `eml`, `txt`). | `tc002_document_attach.py`, `dms/common.py` |
| **AI & OCR Verification** | Validating document OCR indexing in search and testing LLM-driven document intelligence ("Chat with PDF"). | `tc037_document_ocr.py`, `tc136_pdf_document_ocr_from_advanced_search.py`, `tc139_chat_with_pdf.py` |
| **Batch Runner Architecture** | Process isolation via `subprocess`, individual log streaming, regex filtering, and automated failure aggregation. | `robo2_test_cases/dms/run_all.py` |
| **Desktop Application Engineering** | Custom Tkinter GUI with Per-Monitor High-DPI awareness, multi-threading (`threading`, `queue.Queue`), and live execution metrics. | `robo2_test_cases/dms/app_gui.py` |
| **Application Packaging & CI/CD** | PyInstaller build script compiling the automation engine and UI into a standalone Windows binary (`.exe`). | `dms/build_exe.py`, `dms/build_exe.bat`, `dms/Robo2mation_Runner.spec` |
| **Data-Driven Excel Reporting** | Automated workbook manipulation with `openpyxl`: cell updating, status rollups, hyperlink evidence injection, and summary recount. | `login/common.py` → `write_excel()`, `dms/common.py` |
| **Secure Configuration** | Zero credential leaks: 100% environment separation via `python-dotenv` and comprehensive `.gitignore` rules. | `.env.example`, `.gitignore` |
| **Web Scraping & Export** | Headless Chrome navigation, multi-field data extraction, simultaneous file/console logging, CSV/JSON serialization. | `login-and-scrape-automation/scraper.py` |

---

## 📁 Repository Architecture

```
Selenium/
├── .gitignore                                  # Comprehensive ignore list (secrets, logs, temp files)
├── readme.md                                   # Root project documentation
│
├── login-and-scrape-automation/                # Public Target Scraping & Login Automation
│   ├── scraper.py                              # Main scraping script (SauceDemo target)
│   ├── requirements.txt                        # Scraper dependencies (selenium, python-dotenv)
│   ├── .env.example                            # Configuration template (credentials, headless mode)
│   └── output/                                 # Generated exports (git-ignored)
│       ├── items_*.csv                         # Scraped product catalog in CSV format
│       ├── items_*.json                        # Scraped product catalog in JSON format
│       ├── page_*.png                          # Verification screenshots
│       └── run.log                             # Detailed execution logs
│
└── robo2_test_cases/                           # Robo2mation ECM Sanity Automation Framework
    ├── .env.example                            # Root environment template for login suite
    ├── Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx   # Official Excel test case tracking sheet (git-ignored for lock safety)
    ├── Robo2mation_26Q1_Sanity_Test_Case_Doc2.xlsx  # Secondary execution tracking sheet (git-ignored for lock safety)
    │
    ├── login/                                  # Core Authentication Test Suite
    │   ├── common.py                           # Shared harness: login(), write_excel(), run_test()
    │   ├── login_valid.py                      # Test COR-TC001: Valid user dashboard redirection
    │   └── login_invalid.py                    # Test COR-TC002: Invalid user error banner validation
    │
    └── dms/                                    # Document Management System (DMS) Suite
        ├── app_gui.py                          # High-DPI Tkinter Desktop Test Runner Client
        ├── run_all.py                          # CLI Process-isolated batch test runner
        ├── build_exe.py                        # Automated PyInstaller build script
        ├── build_exe.bat                       # One-click Windows build batch file
        ├── Robo2mation_Runner.spec             # PyInstaller compilation specification
        ├── assets/                             # GUI branding & High-DPI icons (app.ico, multi-res logos)
        ├── common.py                           # Core DMS harness (waits, Excel, navigation, session)
        ├── dms_helper.py                       # Advanced feature helpers (watermark, taxonomy, review)
        ├── explorer_helper.py                  # My Documents tree navigation & AJAX wait helpers
        ├── .env.example                        # Comprehensive DMS environment variables template
        ├── test_files/                         # Sample upload artifacts for 18 extensions (git-ignored)
        ├── logs/                               # Per-test isolated stdout/stderr logs (git-ignored)
        ├── screenshots/                        # Captured pass/fail screenshots (git-ignored)
        └── tc*.py                              # 85 automated DMS test scripts (tc002 to tc139)
```

---

## 📦 Core Projects

### 1. Robo2mation DMS Enterprise Test Suite (85 Tests)

**Location:** [`robo2_test_cases/dms/`](robo2_test_cases/dms/)

A comprehensive end-to-end automation suite for the Robo2mation Enterprise Content Management platform. The suite models real-world business document lifecycles through modular, maintainable Selenium scripts:

#### Functional Test Coverage Matrix

| Functional Area | Test Cases | Scope & Validation Logic |
|---|---|---|
| **Multi-Format Attachments** | `tc002` | Validates file upload handling across 18 unique extensions (`pdf`, `png`, `jpg`, `jpeg`, `svg`, `gif`, `mp3`, `mp4`, `doc`, `docx`, `xls`, `xlsx`, `csv`, `ppt`, `pptx`, `msg`, `eml`, `txt`). |
| **Document Ingestion, Naming & Viewer** | `tc003`, `tc009`, `tc012`, `tc024`, `tc055`, `tc056` | Verifies single document uploads with mandatory metadata, thumbnail rendering, automated document naming conventions (`tc012`), full-screen document viewing in new tabs, and Grid vs. List views. |
| **Document Downloads & PDF Merging** | `tc011` (runner & helper), `tc022`, `tc023` | Validates multi-PDF merging into single assets, single document downloads (`tc022`), and multi-document batch downloads packaged into `.zip` archives. |
| **Document Versioning** | `tc014`, `tc015`, `tc016` | Tests version progression upon new file uploads, downloading historical document versions, and deleting specific revisions. |
| **Check-Out / Check-In Concurrency** | `tc020`, `tc021` | Enforces document locking during editing (check-out) and verifies state restoration when check-out is cancelled. |
| **Document Lifecycle & Trash** | `tc025`, `tc026`, `tc027`, `tc028` | Validates document archival, archive retrieval, soft-deletion into the trash bin, and item recovery back to active directories. |
| **Related Documents & Links** | `tc030`, `tc031` | Tests cross-linking related files to documents and deleting associated relationship links. |
| **Access Control & Secure Sharing** | `tc032`, `tc033`, `tc034`, `tc036` | Tests document sharing with internal users/groups, generating public external links, revoking shared access, and emailing document links. |
| **Watermarking & Security** | `tc042`, `tc045`, `tc046`, `tc049`, `tc050` | Automates applying custom text watermarks, uploading image watermarks, searching watermark templates, attaching watermarks to documents, and watermark removal. |
| **Directory Navigation & Sorting** | `tc051`, `tc057`–`tc062` | Tests "My Documents" tree navigation, alphabetical sorting (ascending/descending), chronological sorting, and category grouping. |
| **Taxonomy & Category Administration** | `tc067`, `tc069`, `tc073`, `tc075`–`tc078` | Automates category and document-type creation, updating taxonomy nodes, hierarchical deletion, category map audits, restoration, and permanent removal. |
| **Governance & Access Assignment** | `tc080`, `tc081`, `tc082`, `tc083`, `tc084` | Tests publishing document types, assigning access groups, assigning owner groups, and toggling automated document email notifications. |
| **Metadata Management & Rules** | `tc019`, `tc085`, `tc086`, `tc087`, `tc090`, `tc091`, `tc092` | Automates dynamic metadata field creation, in-place metadata updates (`tc019`), schema deletions, and validates uniqueness rules under both `OR` and `AND` boolean conditions. |
| **Bulk Processing & Ingestion** | `tc093`, `tc094`, `tc095`, `tc132` | Tests downloading bulk upload Excel templates, uploading invalid format templates (negative testing), uploading valid templates, and automated bulk document ingest. |
| **Master Table Data Methods** | `tc101`–`tc110`, `tc112` | Tests CRUD operations on Master Tables: fetching single/multiple records, updating records, deleting, filtering by doc-type, searching, disabling/enabling records, cloning, and assigning. |
| **Search Engine & Saved Queries** | `tc119`, `tc121`, `tc122`, `tc124`, `tc125`, `tc126` | Verifies quick global search, advanced search with "Match All" criteria toggle, archived documents search filter, saving search queries, and retrieving saved search lists. |
| **Maker-Checker Workflow Gate** | `tc127`, `tc128`, `tc130`, `tc131` | Multi-user end-to-end workflow: Maker submits a document for review; system verifies "Pending for Review Requested by Me"; Checker logs in, reviews the document, and executes Approve/Reject decisions. |
| **AI & Optical Character Recognition** | `tc037`, `tc136`, `tc137`, `tc139` | Verifies OCR extraction on scanned PDFs, advanced search OCR indexing, and validates "Chat with PDF" (Ask Effy AI LLM assistant) document querying. |

---

### 2. Desktop GUI Test Runner & Executable Packaging

**Location:** [`robo2_test_cases/dms/app_gui.py`](robo2_test_cases/dms/app_gui.py)

To empower non-technical QA engineers and release managers, the repository provides a standalone desktop runner client and automated build pipeline:

- **Tkinter Desktop Client (`app_gui.py`)**:
  - **High-DPI Awareness**: Utilizes Windows `shcore.SetProcessDpiAwareness(2)` for crisp typography on 4K/retina displays.
  - **Module Selection**: Switch between DMS, Core, Workflow, Report, and Configurable suites.
  - **Interactive Execution**: Select all tests or cherry-pick specific scenarios with a checkbox tree.
  - **Live Execution Feedback**: Threaded background workers communicate over `queue.Queue` to render live execution charts, progress bars, and streaming console logs without freezing the UI.
  - **Process-Isolated Subprocess Worker**: Invokes tests via `--worker-test <script> <sheet>` to ensure browser crashes do not affect the GUI harness.
- **CLI Batch Test Runner (`run_all.py`)**:
  - Executes test cases consecutively in independent Chrome processes.
  - Generates per-test log files in `logs/<script_name>.log`.
  - Supports pattern filtering (e.g., `python run_all.py tc014 tc022`).
  - Configurable execution timeout guards (10-minute cap per test).
- **Standalone Binary Packaging (`build_exe.py` / `build_exe.bat`)**:
  - Packages Python, Selenium, openpyxl, assets, and test scripts into a zero-dependency Windows executable (`dist/Robo2mation_Runner/Robo2mation_Runner.exe`).

---

### 3. Core Authentication Sanity Suite & Excel Tracker

**Location:** [`robo2_test_cases/login/`](robo2_test_cases/login/)

Validates platform authentication and security boundary gates while serving as an automated bridge to enterprise test documentation:

| Test ID | Script | Scenario | Verification Criteria |
|---|---|---|---|
| `COR-TC001` | `login_valid.py` | Valid authentication | Successful submission of valid credentials; verifies password box becomes invisible and user lands on dashboard. |
| `COR-TC002` | `login_invalid.py` | Invalid authentication | Submission of invalid credentials; verifies error alert banner (`.error`, `.alert-danger`, `.swal2-popup`) is rendered and user remains unauthenticated. |

#### Two-Way Excel Tracker Synchronization (`common.py` → `write_excel()`)
- Scans `Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx` for the target `tc_id`.
- Populates the **Status** (`Pass` / `Fail`), **Actual Result** description, **Evidence** screenshot path, **Execution Date**, and **Tester Name**.
- Dynamically recalculates the summary dashboard counters:
  - Cell `D2`: Total Executed Tests
  - Cell `F2`: Total Passed Tests
  - Cell `H2`: Total Failed Tests
- Automatically saves evidence screenshots into `screenshots/<tc_id>.png`.

---

### 4. Web Scraping & E2E Extraction Automation

**Location:** [`login-and-scrape-automation/`](login-and-scrape-automation/)

A clean, standalone web scraper and end-to-end automation tool built for [SauceDemo](https://www.saucedemo.com):
- **Authentication**: Dynamic credential loading via environment variables.
- **Resilient Locators**: Centralized locator dictionary (`SELECTORS`) minimizing maintenance overhead.
- **Data Pipeline**: Scrapes inventory item titles and pricing into structured Python dictionaries.
- **Multi-Format Export**: Generates timestamped `.json` and `.csv` files in `output/`.
- **Audit & Diagnostics**: Takes a full-page verification screenshot and writes execution telemetry to `output/run.log` and console simultaneously.

---

## 🛠 Tech Stack & Dependencies

| Technology | Version / Requirement | Role in Project |
|---|---|---|
| **Python** | `3.10+` (tested on `3.15`) | Core programming language |
| **Selenium WebDriver** | `4.x` (e.g., `4.51.0`) | Browser automation, user interactions, explicit synchronization |
| **ChromeDriver / Selenium Manager** | Automatic | Automated driver binary resolution via Selenium Manager |
| **openpyxl** | `3.1.x` | Programmatic reading and writing of Excel test case trackers |
| **python-dotenv** | `1.x` | Secure environment variable and credential configuration |
| **Tkinter** | Standard Library | Graphical User Interface for desktop test runner |
| **PyInstaller** | `6.x` | Packaging test harness into standalone Windows executables |

---

## ⚡ Prerequisites & Environment Setup

### 1. Prerequisites
- **Operating System**: Windows 10/11 recommended (Linux/macOS supported for scraper).
- **Python**: Python 3.10 or higher installed with `pip` added to your system `PATH`.
- **Google Chrome**: Latest stable version installed. (Selenium Manager handles the matching ChromeDriver automatically).

### 2. Clone the Repository
```bash
git clone https://github.com/ays19/Selenium.git
cd Selenium
```

### 3. Create and Activate a Virtual Environment
```bash
# Windows (Command Prompt / PowerShell)
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
You can install all dependencies across the repository with a single command:
```bash
pip install selenium python-dotenv openpyxl pyinstaller
```

Or install dependencies per module:
```bash
# For login and scrape automation
cd login-and-scrape-automation
pip install -r requirements.txt
cd ..
```

---

## 🚀 Step-by-Step Execution Guide

### Quick Start: SauceDemo Automation (No Credentials Required)
This project requires no private infrastructure. You can run it immediately after cloning:

```bash
cd login-and-scrape-automation

# Copy environment configuration
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Execute scraper
python scraper.py
```
*Outputs will be saved in `login-and-scrape-automation/output/`.*

---

### Running the Core Login Tests
To run the authentication sanity tests against the Excel tracker:

```bash
cd robo2_test_cases/login

# Create .env from root template
copy ..\.env.example .env     # Windows
# cp ../.env.example .env     # macOS / Linux

# Open .env and set your SITE_URL, VALID_USER, VALID_PASS, TESTER_NAME,
# and set EXCEL_FILE=../Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx
# Run individual tests:
python login_valid.py
python login_invalid.py
```
*Results and screenshots will be written directly to `Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx`.*

---

### Running the DMS Suite via CLI Batch Runner
The batch runner executes DMS test cases in isolated processes:

```bash
cd robo2_test_cases/dms

# Create .env from template
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# Configure your BASE_URL, DMS_USERNAME, DMS_PASSWORD, TESTER_NAME,
# and set EXCEL_PATH=../Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx in .env
# Place required test files in test_files/ (e.g., sample.pdf, sample.png, etc.)

# Run ALL DMS test cases sequentially:
python run_all.py

# Run only specific test cases (by prefix):
python run_all.py tc002 tc014 tc022
```
*Per-test logs are stored in `robo2_test_cases/dms/logs/`.*

---

### Launching the Desktop GUI Runner
For an interactive, visual test management experience:

```bash
cd robo2_test_cases/dms
python app_gui.py
```
1. Select the target module (e.g., **DMS**).
2. Use the checkboxes to select all or individual test cases.
3. Click **Run Selected Tests**.
4. Monitor live test execution, charts, and console logs.

---

### Compiling Standalone Executable (PyInstaller)
To compile the test suite into a standalone Windows application:

```bash
cd robo2_test_cases/dms

# Option A: Run the batch file
build_exe.bat

# Option B: Run via Python
python build_exe.py
```
*The compiled application is generated in `robo2_test_cases/dms/dist/Robo2mation_Runner/`.*

---

## 🛡️ QA Engineering Patterns & Best Practices

1. **Explicit Synchronization Over Arbitrary Sleeps**
   - Uses `WebDriverWait` paired with `EC.visibility_of_element_located`, `EC.element_to_be_clickable`, or custom dynamic lambdas.
   - Eliminates race conditions and avoids flaky tests caused by hardcoded `time.sleep()`.

2. **Process Isolation in Test Runners**
   - By running each test script in a separate Python process via `subprocess.run()`, unhandled browser exceptions, memory leaks, or hung sessions cannot terminate the entire test suite.

3. **Multi-User Maker-Checker Authorization Testing**
   - Validates segregation of duties by initiating a request under a "Maker" account, terminating/switching the browser session, and completing approval/rejection under an independent "Checker" account.

4. **Bi-Directional Test Management Synchronization**
   - Automatically synchronizes test outcomes directly into client-facing Excel workbooks, eliminating manual data entry and human error in QA sign-offs.

5. **Defensive Resource Cleanup**
   - Test execution blocks guarantee browser closure via `finally: driver.quit()`, preventing orphaned `chromedriver.exe` processes from consuming system resources.

6. **Strict Secret Hygiene**
   - Sensitive credentials, API keys, and environment-specific endpoints are isolated in `.env` files. The `.gitignore` excludes all `.env` files, temporary artifacts, and office lockfiles (`~$*`).

---

## ❓ Troubleshooting & FAQ

- **Error: `FileNotFoundError: [Errno 2] No such file or directory` on Excel file**
  - **Cause**: The `EXCEL_FILE` or `EXCEL_PATH` variable in `.env` is resolved relative to the active working directory from which Python was launched.
  - **Fix**: When running inside subdirectories (`robo2_test_cases/login/` or `robo2_test_cases/dms/`), ensure the path points one folder up (`../Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx`) or provide an absolute path.
- **Error: `PermissionError: [WinError 5] Access is denied` on Excel file**
  - **Cause**: Excel has the `.xlsx` tracker open in Microsoft Excel, locking the file from write operations.
  - **Fix**: Close Microsoft Excel before running tests.
- **Error: `Missing sample files in test_files/` during attachment tests**
  - **Cause**: `tc002_document_attach.py` verifies that sample files exist for all 18 extensions before launching the browser.
  - **Fix**: Populate `robo2_test_cases/dms/test_files/` with sample files for each extension (`sample.pdf`, `sample.docx`, etc.).
- **Browser fails to launch or ChromeDriver mismatch**
  - **Fix**: Selenium 4.6+ automatically manages drivers via Selenium Manager. Ensure your machine has internet access on first run so Selenium Manager can fetch the matching driver.
- **Blurry desktop GUI on high-resolution displays**
  - **Fix**: High-DPI scaling is automatically enabled in `app_gui.py` via `ctypes.windll.shcore.SetProcessDpiAwareness(2)`. Ensure you run on Windows 10/11.

---

## 👤 Author & Maintainer
- **Portfolio Repository**: [github.com/ays19/Selenium](https://github.com/ays19/Selenium)
- **Primary Focus**: Enterprise QA Automation, Selenium WebDriver, Test Tooling & Desktop Architecture.
