"""Zero-terminal Allure 2 report generator and quiet local HTTP viewer."""
from __future__ import annotations

from datetime import datetime
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import webbrowser

_ATTACH_TEXT_LIMIT = 32768


def resolve_allure_results_dir(app_dir: Path) -> Path:
    """Return configured Allure results directory (resolved relative to app_dir)."""
    raw = (
        os.getenv("DMS_ALLURE_RESULTS_DIR")
        or os.getenv("ALLURE_RESULTS_DIR")
        or "allure-results"
    ).strip()
    candidate = Path(raw)
    return candidate.resolve() if candidate.is_absolute() else (app_dir / candidate).resolve()


def _has_result_files(folder: Path) -> bool:
    return folder.is_dir() and any(folder.glob("*-result.json"))


def find_results_dir_with_data(app_dir: Path) -> Path | None:
    """Locate primary or fallback Allure results directory containing test results."""
    candidates = [resolve_allure_results_dir(app_dir)]
    fallback = (app_dir.parent.parent / "allure-results").resolve()
    if fallback not in candidates:
        candidates.append(fallback)
    for folder in candidates:
        if _has_result_files(folder):
            return folder
    return None


def find_allure_cli() -> str | None:
    """Find an installed Allure commandline executable without spawning a console."""
    for name in ("allure", "allure.bat", "allure.cmd"):
        found = shutil.which(name)
        if found:
            return found
    allure_home = (os.getenv("ALLURE_HOME") or "").strip()
    if allure_home:
        for exe in ("allure.bat", "allure.cmd", "allure"):
            cand = Path(allure_home) / "bin" / exe
            if cand.is_file():
                return str(cand)
    return None


def generate_allure_cli_report(results_dir: Path, report_dir: Path) -> bool:
    """Generate official Allure HTML report silently when Allure CLI is available."""
    cli = find_allure_cli()
    if not cli:
        return False

    env = os.environ.copy()
    if not env.get("JAVA_HOME"):
        try:
            import jdk4py

            env["JAVA_HOME"] = str(jdk4py.JAVA_HOME)
        except Exception:
            pass

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        proc = subprocess.run(
            [cli, "generate", str(results_dir), "-o", str(report_dir), "--clean"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60,
            creationflags=flags,
        )
        return proc.returncode == 0 and (report_dir / "index.html").is_file()
    except Exception:
        return False


def _prepare_report_dirs(report_dir: Path) -> Path:
    if report_dir.exists():
        shutil.rmtree(report_dir, ignore_errors=True)
    attachments_dir = report_dir / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    return attachments_dir


def _copy_attachment(
    att: dict,
    results_dir: Path,
    results_root: Path,
    attachments_dir: Path,
    copied: set[str],
) -> dict:
    raw_source = str(att.get("source") or "")
    safe_name = Path(raw_source).name
    att_type = str(att.get("type") or "")
    att_name = str(att.get("name") or safe_name or "Attachment")
    record = {"name": att_name, "type": att_type, "relPath": "", "inlineText": ""}

    if not safe_name:
        return record

    src_file = (results_dir / safe_name).resolve()
    try:
        src_file.relative_to(results_root)
    except ValueError:
        return record

    if not src_file.is_file():
        return record

    dst_file = attachments_dir / safe_name
    if safe_name not in copied:
        shutil.copy2(src_file, dst_file)
        copied.add(safe_name)

    record["relPath"] = f"attachments/{safe_name}"
    if "text/plain" in att_type.lower() or src_file.suffix.lower() in (".txt", ".log"):
        try:
            if src_file.stat().st_size <= _ATTACH_TEXT_LIMIT:
                record["inlineText"] = src_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return record


def _normalize_steps(
    raw_steps: list | None,
    results_dir: Path,
    results_root: Path,
    attachments_dir: Path,
    copied: set[str],
) -> list[dict]:
    steps: list[dict] = []
    for raw in raw_steps or []:
        if not isinstance(raw, dict):
            continue
        start = raw.get("start") or 0
        stop = raw.get("stop") or start
        details = raw.get("statusDetails") or {}
        atts = [
            _copy_attachment(a, results_dir, results_root, attachments_dir, copied)
            for a in (raw.get("attachments") or [])
            if isinstance(a, dict)
        ]
        steps.append(
            {
                "name": str(raw.get("name") or "Step"),
                "status": str(raw.get("status") or "unknown").lower(),
                "start": start,
                "stop": stop,
                "durationMs": max(0, int(stop) - int(start)),
                "message": str(details.get("message") or ""),
                "trace": str(details.get("trace") or ""),
                "attachments": atts,
                "steps": _normalize_steps(
                    raw.get("steps"), results_dir, results_root, attachments_dir, copied
                ),
            }
        )
    return steps


def _parse_result_file(
    path: Path,
    results_dir: Path,
    results_root: Path,
    attachments_dir: Path,
    copied: set[str],
) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    start = int(data.get("start") or 0)
    stop = int(data.get("stop") or start)
    details = data.get("statusDetails") or {}
    labels = [
        {"name": str(lb.get("name") or ""), "value": str(lb.get("value") or "")}
        for lb in (data.get("labels") or [])
        if isinstance(lb, dict)
    ]
    links = [
        {
            "name": str(lk.get("name") or lk.get("url") or "Link"),
            "url": str(lk.get("url") or ""),
            "type": str(lk.get("type") or "link"),
        }
        for lk in (data.get("links") or [])
        if isinstance(lk, dict) and lk.get("url")
    ]
    atts = [
        _copy_attachment(a, results_dir, results_root, attachments_dir, copied)
        for a in (data.get("attachments") or [])
        if isinstance(a, dict)
    ]
    feature = next((lb["value"] for lb in labels if lb["name"] == "feature"), "")
    return {
        "uuid": str(data.get("uuid") or path.stem),
        "name": str(data.get("name") or path.stem),
        "testCaseId": str(data.get("testCaseId") or ""),
        "fullName": str(data.get("fullName") or ""),
        "feature": feature,
        "status": str(data.get("status") or "unknown").lower(),
        "description": str(data.get("description") or ""),
        "start": start,
        "stop": stop,
        "durationMs": max(0, stop - start),
        "message": str(details.get("message") or ""),
        "trace": str(details.get("trace") or ""),
        "labels": labels,
        "links": links,
        "steps": _normalize_steps(
            data.get("steps"), results_dir, results_root, attachments_dir, copied
        ),
        "attachments": atts,
    }


def generate_builtin_html_report(results_dir: Path, report_dir: Path) -> Path:
    """Generate a self-contained offline HTML Allure 2 report from allure-results."""
    attachments_dir = _prepare_report_dirs(report_dir)
    results_root = results_dir.resolve()
    copied: set[str] = set()

    tests: list[dict] = []
    for result_file in sorted(results_dir.glob("*-result.json")):
        parsed = _parse_result_file(
            result_file, results_dir, results_root, attachments_dir, copied
        )
        if parsed is not None:
            tests.append(parsed)

    tests.sort(key=lambda item: item.get("start", 0), reverse=True)

    payload = {
        "generatedAt": datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
        "resultsDir": str(results_root),
        "tests": tests,
    }
    safe_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = _HTML_TEMPLATE.replace("__ALLURE_DATA_JSON__", safe_json)

    index_path = report_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP file handler with suppressed logging so --windowed exe never fails."""

    def log_message(self, format: str, *args) -> None:
        return


class AllureReportServer:
    """Quiet daemon localhost server for viewing generated Allure reports."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._server: http.server.ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._report_dir: Path | None = None
        self._port: int = 0

    def serve(self, report_dir: Path) -> str:
        resolved = report_dir.resolve()
        with self._lock:
            if (
                self._server is not None
                and self._thread is not None
                and self._thread.is_alive()
                and self._report_dir == resolved
            ):
                return f"http://127.0.0.1:{self._port}/"

            self._stop_unlocked()
            handler = functools.partial(_QuietHandler, directory=str(resolved))
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            server.daemon_threads = True
            self._port = int(server.server_address[1])
            self._report_dir = resolved
            self._server = server
            self._thread = threading.Thread(
                target=server.serve_forever, daemon=True, name="AllureReportHTTP"
            )
            self._thread.start()
            return f"http://127.0.0.1:{self._port}/"

    def _stop_unlocked(self) -> None:
        if self._server is not None:
            try:
                self._server.shutdown()
            except Exception:
                pass
            try:
                self._server.server_close()
            except Exception:
                pass
        self._server = None
        self._thread = None
        self._report_dir = None
        self._port = 0

    def stop(self) -> None:
        with self._lock:
            self._stop_unlocked()


def open_allure_report(app_dir: Path, server: AllureReportServer) -> tuple[bool, str]:
    """Generate and open the Allure report in the default browser without a terminal."""
    results_dir = find_results_dir_with_data(app_dir)
    if results_dir is None:
        return (
            False,
            "No Allure test results found yet. Run at least one DMS test first.",
        )

    report_dir = results_dir.parent / "allure-report"
    if generate_allure_cli_report(results_dir, report_dir):
        engine = "Allure CLI"
    else:
        generate_builtin_html_report(results_dir, report_dir)
        engine = "Built-in Viewer"

    base_url = server.serve(report_dir)
    url = f"{base_url}?t={int(time.time())}"
    webbrowser.open(url, new=2)
    return True, f"Opened Allure Report ({engine}) from {results_dir} -> {url}"


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Robo2mation DMS — Allure Report</title>
<style>
  :root {
    --bg: #f1f5f9;
    --card: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --muted: #64748b;
    --brand: #1992d0;
    --brand-dark: #0e7ab5;
    --passed: #10b981;
    --passed-bg: #ecfdf5;
    --failed: #ef4444;
    --failed-bg: #fef2f2;
    --broken: #f59e0b;
    --broken-bg: #fffbeb;
    --skipped: #8b5cf6;
    --skipped-bg: #f5f3ff;
    --unknown: #64748b;
    --unknown-bg: #f1f5f9;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.45;
  }
  header {
    background: #ffffff;
    border-bottom: 3px solid var(--brand);
    padding: 16px 24px;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  .title-block h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
  }
  .meta-line {
    font-size: 12px;
    color: var(--muted);
    margin-top: 3px;
    word-break: break-all;
  }
  .rate-pill {
    background: #e8f4fb;
    color: var(--brand-dark);
    font-weight: 700;
    font-size: 14px;
    padding: 6px 14px;
    border-radius: 999px;
    border: 1px solid #bae6fd;
  }
  .container {
    max-width: 1480px;
    margin: 0 auto;
    padding: 16px 20px 24px;
  }
  .overview {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 14px;
    margin-bottom: 14px;
  }
  @media (max-width: 900px) {
    .overview { grid-template-columns: 1fr; }
  }
  .kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(125px, 1fr));
    gap: 10px;
  }
  .kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    border-top: 3px solid var(--brand);
  }
  .kpi.passed { border-top-color: var(--passed); }
  .kpi.failed { border-top-color: var(--failed); }
  .kpi.broken { border-top-color: var(--broken); }
  .kpi.skipped { border-top-color: var(--skipped); }
  .kpi-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    font-weight: 600;
  }
  .kpi-value {
    font-size: 22px;
    font-weight: 700;
    margin-top: 4px;
  }
  .donut-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .donut {
    width: 78px;
    height: 78px;
    border-radius: 50%;
    position: relative;
    flex-shrink: 0;
  }
  .donut-hole {
    position: absolute;
    inset: 14px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
  }
  .legend { font-size: 12px; display: grid; gap: 3px; }
  .legend-item { display: flex; align-items: center; gap: 6px; color: #334155; }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }

  .toolbar {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 14px;
  }
  .pills { display: flex; flex-wrap: wrap; gap: 6px; }
  .pill {
    border: 1px solid var(--border);
    background: #f8fafc;
    color: #334155;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 11px;
    border-radius: 999px;
    cursor: pointer;
  }
  .pill.active {
    background: var(--brand);
    color: #fff;
    border-color: var(--brand);
  }
  .controls-right {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .search-box {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 11px;
    font-size: 13px;
    min-width: 240px;
    outline: none;
  }
  .search-box:focus { border-color: var(--brand); }
  .mode-btn {
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #1e293b;
    padding: 6px 11px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }
  .mode-btn.latest {
    background: #e8f4fb;
    border-color: #7dd3fc;
    color: var(--brand-dark);
  }

  .split {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 14px;
    align-items: start;
  }
  @media (max-width: 980px) {
    .split { grid-template-columns: 1fr; }
  }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .list-panel {
    max-height: calc(100vh - 280px);
    min-height: 460px;
    overflow-y: auto;
  }
  .test-item {
    padding: 11px 14px;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    transition: background 0.12s;
  }
  .test-item:hover { background: #f8fafc; }
  .test-item.active {
    background: #e8f4fb;
    border-left: 4px solid var(--brand);
    padding-left: 10px;
  }
  .test-row-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
  }
  .test-name { font-size: 13px; font-weight: 600; color: #0f172a; }
  .test-meta {
    margin-top: 4px;
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--muted);
  }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    white-space: nowrap;
  }
  .st-passed { background: var(--passed-bg); color: #047857; }
  .st-failed { background: var(--failed-bg); color: #b91c1c; }
  .st-broken { background: var(--broken-bg); color: #b45309; }
  .st-skipped { background: var(--skipped-bg); color: #6d28d9; }
  .st-unknown { background: var(--unknown-bg); color: #475569; }

  .detail-panel {
    padding: 18px 20px;
    min-height: 460px;
  }
  .detail-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-start;
    gap: 10px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
    margin-bottom: 14px;
  }
  .detail-title { font-size: 18px; font-weight: 700; margin: 0; }
  .sub-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
    font-size: 12px;
    color: var(--muted);
  }
  .tag {
    background: #f1f5f9;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    color: #334155;
  }
  .link-tag {
    background: #e8f4fb;
    border: 1px solid #bae6fd;
    color: var(--brand-dark);
    text-decoration: none;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
  }
  .msg-box {
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 12px;
    font-size: 13px;
    border-left: 4px solid;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg-box.passed { background: var(--passed-bg); border-color: var(--passed); color: #065f46; }
  .msg-box.failed { background: var(--failed-bg); border-color: var(--failed); color: #991b1b; }
  .msg-box.broken { background: var(--broken-bg); border-color: var(--broken); color: #92400e; }
  .msg-box.skipped { background: var(--skipped-bg); border-color: var(--skipped); color: #5b21b6; }

  .sec-title {
    font-size: 13px;
    font-weight: 700;
    color: #1e293b;
    margin: 14px 0 8px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 12px;
    overflow-x: auto;
    margin: 6px 0;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .desc-pre {
    background: #f8fafc;
    color: #334155;
    border: 1px solid var(--border);
    font-family: "Segoe UI", sans-serif;
  }
  details summary {
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    color: var(--brand-dark);
    margin: 6px 0;
  }
  .step-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 11px;
    margin-bottom: 6px;
    background: #ffffff;
  }
  .step-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }
  .step-children {
    margin-top: 8px;
    margin-left: 14px;
    padding-left: 10px;
    border-left: 2px solid #e2e8f0;
  }
  .att-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 10px;
  }
  .att-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px;
    background: #f8fafc;
  }
  .att-thumb {
    width: 100%;
    height: 130px;
    object-fit: cover;
    border-radius: 6px;
    cursor: zoom-in;
    border: 1px solid #cbd5e1;
    background: #fff;
  }
  .att-name {
    font-size: 11px;
    font-weight: 600;
    color: #334155;
    margin-top: 6px;
    word-break: break-word;
  }
  .att-btn {
    display: inline-block;
    margin-top: 6px;
    padding: 4px 9px;
    border-radius: 6px;
    background: var(--brand);
    color: #fff;
    text-decoration: none;
    font-size: 11px;
    font-weight: 600;
  }
  .hist-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 5px;
    font-size: 12px;
    cursor: pointer;
    background: #f8fafc;
  }
  .hist-row:hover { background: #e8f4fb; }
  .empty {
    padding: 28px;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
  }
  .lightbox {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.85);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 20px;
    cursor: zoom-out;
  }
  .lightbox.open { display: flex; }
  .lightbox img {
    max-width: 96vw;
    max-height: 92vh;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    background: #fff;
  }
</style>
</head>
<body>
<header>
  <div class="title-block">
    <h1>Robo2mation DMS — Allure Report</h1>
    <div class="meta-line" id="headerMeta"></div>
  </div>
  <div class="rate-pill" id="passRatePill">Pass Rate: 0%</div>
</header>

<div class="container">
  <div class="overview">
    <div class="kpis" id="kpiGrid"></div>
    <div class="donut-card">
      <div class="donut" id="donutChart"><div class="donut-hole" id="donutLabel">0%</div></div>
      <div class="legend" id="donutLegend"></div>
    </div>
  </div>

  <div class="toolbar">
    <div class="pills" id="statusPills"></div>
    <div class="controls-right">
      <input class="search-box" id="searchInput" type="search" placeholder="Search test ID, name, feature, message..." />
      <button class="mode-btn latest" id="modeToggleBtn" type="button">Showing: Latest per Test</button>
    </div>
  </div>

  <div class="split">
    <div class="panel list-panel" id="testList"></div>
    <div class="panel detail-panel" id="testDetail"></div>
  </div>
</div>

<div class="lightbox" id="lightbox" onclick="this.classList.remove('open')">
  <img id="lightboxImg" src="" alt="Screenshot preview" />
</div>

<script>
const REPORT_DATA = __ALLURE_DATA_JSON__;

const state = {
  status: "all",
  search: "",
  latestOnly: true,
  selectedUuid: null
};

function escHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function fmtDuration(ms) {
  const sec = Math.max(0, Number(ms || 0)) / 1000;
  if (sec < 60) return sec.toFixed(sec >= 10 ? 1 : 2) + "s";
  const m = Math.floor(sec / 60);
  const rem = sec % 60;
  return m + "m " + rem.toFixed(0) + "s";
}

function fmtTime(ms) {
  if (!ms) return "—";
  try {
    return new Date(Number(ms)).toLocaleString();
  } catch (e) {
    return String(ms);
  }
}

function testKey(t) {
  return (t.testCaseId || t.fullName || t.name || t.uuid).toLowerCase();
}

function getBaseTests() {
  const all = REPORT_DATA.tests || [];
  if (!state.latestOnly) return all;
  const seen = new Set();
  const dedup = [];
  for (const t of all) {
    const k = testKey(t);
    if (!seen.has(k)) {
      seen.add(k);
      dedup.push(t);
    }
  }
  return dedup;
}

function getHistoryFor(t) {
  const k = testKey(t);
  return (REPORT_DATA.tests || []).filter(item => testKey(item) === k);
}

function renderOverview(base) {
  const counts = { total: base.length, passed: 0, failed: 0, broken: 0, skipped: 0, unknown: 0 };
  let totalMs = 0;
  for (const t of base) {
    totalMs += Number(t.durationMs || 0);
    if (counts[t.status] != null) counts[t.status]++;
    else counts.unknown++;
  }
  const passRate = counts.total ? (counts.passed / counts.total) * 100 : 0;
  document.getElementById("passRatePill").textContent = "Pass Rate: " + passRate.toFixed(1) + "%";

  const cards = [
    ["Total Tests", counts.total, ""],
    ["Passed", counts.passed, "passed"],
    ["Failed", counts.failed, "failed"],
    ["Broken", counts.broken, "broken"],
    ["Skipped", counts.skipped, "skipped"],
    ["Total Time", fmtDuration(totalMs), ""]
  ];
  document.getElementById("kpiGrid").innerHTML = cards
    .map(([lbl, val, cls]) => `<div class="kpi ${cls}"><div class="kpi-label">${lbl}</div><div class="kpi-value">${escHtml(val)}</div></div>`)
    .join("");

  const segments = [
    ["Passed", counts.passed, "#10b981"],
    ["Failed", counts.failed, "#ef4444"],
    ["Broken", counts.broken, "#f59e0b"],
    ["Skipped", counts.skipped, "#8b5cf6"],
    ["Unknown", counts.unknown, "#64748b"]
  ];
  let grad = "#e2e8f0 0 100%";
  if (counts.total > 0) {
    let cursor = 0;
    const parts = [];
    for (const [, val, col] of segments) {
      if (!val) continue;
      const next = cursor + (val / counts.total) * 100;
      parts.push(`${col} ${cursor.toFixed(2)}% ${next.toFixed(2)}%`);
      cursor = next;
    }
    grad = parts.join(", ");
  }
  document.getElementById("donutChart").style.background = `conic-gradient(${grad})`;
  document.getElementById("donutLabel").textContent = passRate.toFixed(0) + "%";
  document.getElementById("donutLegend").innerHTML = segments
    .filter(([, val]) => val > 0)
    .map(([lbl, val, col]) => `<div class="legend-item"><span class="dot" style="background:${col}"></span>${lbl}: <b>${val}</b></div>`)
    .join("") || `<div class="legend-item">No results</div>`;

  const pills = [
    ["all", "All", counts.total],
    ["passed", "Passed", counts.passed],
    ["failed", "Failed", counts.failed],
    ["broken", "Broken", counts.broken],
    ["skipped", "Skipped", counts.skipped]
  ];
  document.getElementById("statusPills").innerHTML = pills
    .map(([k, lbl, c]) => `<button class="pill ${state.status === k ? "active" : ""}" data-status="${k}">${lbl} (${c})</button>`)
    .join("");
  document.querySelectorAll("#statusPills .pill").forEach(btn => {
    btn.onclick = () => { state.status = btn.dataset.status; renderAll(); };
  });
}

function getFilteredTests(base) {
  const q = state.search.trim().toLowerCase();
  return base.filter(t => {
    if (state.status !== "all" && t.status !== state.status) return false;
    if (!q) return true;
    const hay = `${t.testCaseId} ${t.name} ${t.feature} ${t.message}`.toLowerCase();
    return hay.includes(q);
  });
}

function renderSteps(steps) {
  if (!steps || !steps.length) return "";
  return steps.map(st => {
    const cls = "st-" + (["passed", "failed", "broken", "skipped"].includes(st.status) ? st.status : "unknown");
    const err = st.message ? `<div class="msg-box ${escHtml(st.status)}" style="margin-top:6px;margin-bottom:0">${escHtml(st.message)}</div>` : "";
    const trace = st.trace ? `<details><summary>Step Traceback</summary><pre>${escHtml(st.trace)}</pre></details>` : "";
    const atts = renderAttachments(st.attachments);
    const children = st.steps && st.steps.length ? `<div class="step-children">${renderSteps(st.steps)}</div>` : "";
    return `
      <div class="step-card">
        <div class="step-head">
          <span><span class="badge ${cls}">${escHtml(st.status)}</span> &nbsp;${escHtml(st.name)}</span>
          <span style="color:#64748b;font-size:11px;white-space:nowrap">${fmtDuration(st.durationMs)}</span>
        </div>
        ${err}${trace}${atts}${children}
      </div>`;
  }).join("");
}

function renderAttachments(atts) {
  if (!atts || !atts.length) return "";
  const cards = atts.map(a => {
    const lowType = (a.type || "").toLowerCase();
    const lowPath = (a.relPath || "").toLowerCase();
    if (!a.relPath && !a.inlineText) {
      return `<div class="att-card"><div class="att-name">${escHtml(a.name)} (file unavailable)</div></div>`;
    }
    if (lowType.startsWith("image/") || /\.(png|jpg|jpeg|gif|webp)$/.test(lowPath)) {
      return `
        <div class="att-card">
          <img class="att-thumb" src="${escHtml(a.relPath)}" alt="${escHtml(a.name)}" onclick="openLightbox('${escHtml(a.relPath)}')" />
          <div class="att-name">${escHtml(a.name)}</div>
        </div>`;
    }
    if (a.inlineText || lowType.startsWith("text/plain")) {
      const preview = a.inlineText ? `<details><summary>View Text (${escHtml(a.name)})</summary><pre>${escHtml(a.inlineText)}</pre></details>` : "";
      const link = a.relPath ? `<a class="att-btn" href="${escHtml(a.relPath)}" target="_blank" rel="noopener">Open File</a>` : "";
      return `<div class="att-card"><div class="att-name">${escHtml(a.name)}</div>${preview}${link}</div>`;
    }
    return `
      <div class="att-card">
        <div class="att-name">${escHtml(a.name)}</div>
        <a class="att-btn" href="${escHtml(a.relPath)}" target="_blank" rel="noopener">Open Attachment</a>
      </div>`;
  }).join("");
  return `<div class="att-grid" style="margin-top:8px">${cards}</div>`;
}

function openLightbox(src) {
  document.getElementById("lightboxImg").src = src;
  document.getElementById("lightbox").classList.add("open");
}
window.openLightbox = openLightbox;

function renderDetail(t) {
  const el = document.getElementById("testDetail");
  if (!t) {
    el.innerHTML = `<div class="empty">Select a test case on the left to inspect steps, errors, tracebacks, and screenshots.</div>`;
    return;
  }
  const cls = "st-" + (["passed", "failed", "broken", "skipped"].includes(t.status) ? t.status : "unknown");
  const linksHtml = (t.links || []).map(l => `<a class="link-tag" href="${escHtml(l.url)}" target="_blank" rel="noopener">${escHtml(l.name)}</a>`).join("");
  const labelsHtml = (t.labels || []).map(lb => `<span class="tag">${escHtml(lb.name)}: <b>${escHtml(lb.value)}</b></span>`).join("");
  const msgHtml = t.message ? `<div class="msg-box ${escHtml(t.status)}">${escHtml(t.message)}</div>` : "";
  const traceHtml = t.trace ? `<details open><summary>Traceback</summary><pre>${escHtml(t.trace)}</pre></details>` : "";
  const descHtml = t.description ? `<div class="sec-title">Scenario</div><pre class="desc-pre">${escHtml(t.description)}</pre>` : "";
  const stepsHtml = t.steps && t.steps.length ? `<div class="sec-title">Execution Steps (${t.steps.length})</div>${renderSteps(t.steps)}` : "";
  const attHtml = t.attachments && t.attachments.length ? `<div class="sec-title">Attachments (${t.attachments.length})</div>${renderAttachments(t.attachments)}` : "";

  const history = getHistoryFor(t);
  let historyHtml = "";
  if (history.length > 1) {
    const rows = history.map(h => {
      const hCls = "st-" + (["passed", "failed", "broken", "skipped"].includes(h.status) ? h.status : "unknown");
      const currentMark = h.uuid === t.uuid ? " (viewing)" : "";
      return `
        <div class="hist-row" onclick="selectUuid('${escHtml(h.uuid)}')">
          <span><span class="badge ${hCls}">${escHtml(h.status)}</span> &nbsp;${escHtml(fmtTime(h.start))}${currentMark}</span>
          <span>${fmtDuration(h.durationMs)}</span>
        </div>`;
    }).join("");
    historyHtml = `<details style="margin-top:14px"><summary>Execution History (${history.length} runs)</summary>${rows}</details>`;
  }

  el.innerHTML = `
    <div class="detail-header">
      <div>
        <h2 class="detail-title">${escHtml(t.name)}</h2>
        <div class="sub-meta">
          <span>Started: <b>${escHtml(fmtTime(t.start))}</b></span>
          <span>Duration: <b>${fmtDuration(t.durationMs)}</b></span>
          ${linksHtml}
        </div>
        <div class="sub-meta">${labelsHtml}</div>
      </div>
      <span class="badge ${cls}" style="font-size:13px;padding:5px 12px">${escHtml(t.status)}</span>
    </div>
    ${msgHtml}${traceHtml}${descHtml}${stepsHtml}${attHtml}${historyHtml}
  `;
}

function selectUuid(uuid) {
  state.selectedUuid = uuid;
  renderAll();
}
window.selectUuid = selectUuid;

function renderAll() {
  const base = getBaseTests();
  renderOverview(base);
  const visible = getFilteredTests(base);
  const all = REPORT_DATA.tests || [];

  let activeTest = all.find(t => t.uuid === state.selectedUuid);
  if (!activeTest || !visible.some(t => t.uuid === activeTest.uuid)) {
    const existsInAll = activeTest && getHistoryFor(activeTest).some(h => visible.some(v => testKey(v) === testKey(h)));
    if (!existsInAll) {
      activeTest = visible[0] || null;
      state.selectedUuid = activeTest ? activeTest.uuid : null;
    }
  }

  const listEl = document.getElementById("testList");
  if (!visible.length) {
    listEl.innerHTML = `<div class="empty">No matching test results.</div>`;
  } else {
    listEl.innerHTML = visible.map(t => {
      const cls = "st-" + (["passed", "failed", "broken", "skipped"].includes(t.status) ? t.status : "unknown");
      const isActive = activeTest && testKey(t) === testKey(activeTest);
      return `
        <div class="test-item ${isActive ? "active" : ""}" onclick="selectUuid('${escHtml(t.uuid)}')">
          <div class="test-row-top">
            <div class="test-name">${escHtml(t.name)}</div>
            <span class="badge ${cls}">${escHtml(t.status)}</span>
          </div>
          <div class="test-meta">
            <span>${escHtml(t.feature || "DMS")}</span>
            <span>${fmtDuration(t.durationMs)}</span>
          </div>
        </div>`;
    }).join("");
  }
  renderDetail(activeTest);
}

document.getElementById("headerMeta").textContent =
  `Generated: ${REPORT_DATA.generatedAt || ""}   |   Results: ${REPORT_DATA.resultsDir || ""}   |   Executions stored: ${(REPORT_DATA.tests || []).length}`;

document.getElementById("searchInput").oninput = e => {
  state.search = e.target.value || "";
  renderAll();
};

document.getElementById("modeToggleBtn").onclick = () => {
  state.latestOnly = !state.latestOnly;
  const btn = document.getElementById("modeToggleBtn");
  btn.textContent = state.latestOnly ? "Showing: Latest per Test" : "Showing: All Executions";
  btn.classList.toggle("latest", state.latestOnly);
  renderAll();
};

document.addEventListener("keydown", e => {
  if (e.key === "Escape") document.getElementById("lightbox").classList.remove("open");
});

renderAll();
</script>
</body>
</html>
"""
