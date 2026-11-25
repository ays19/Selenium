"""Page Object for the DMS Bulk Upload screen."""
from __future__ import annotations

import csv
from datetime import datetime
import os
import random
import re
import shutil
import tempfile
import time

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class BulkUploadPage(BasePage):
    """Encapsulates Bulk Upload doc-type selection, CSV template download, and submission."""

    SELECT_ID = "document_type_bulk_upload"

    def open(self) -> None:
        self.driver.get(cfg.BULK_URL)
        self.wait_for_page_load()

    def pick_bulk_doc_type(self, term: str) -> None:
        self.open()
        box = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"span.select2-selection[aria-labelledby='select2-{self.SELECT_ID}-container']")
            )
        )
        self.click(box)
        search = self.wait.until(
            EC.visibility_of_element_located((
                By.XPATH,
                f"//ul[@id='select2-{self.SELECT_ID}-results']/ancestor::span[contains(@class, 'select2-dropdown')]"
                "//input[contains(@class, 'select2-search__field')]",
            ))
        )
        search.click()
        typed = term.strip().strip("/").split("/")[-1]
        for letter in typed[:30]:
            search.send_keys(letter)
            time.sleep(0.15)

        option_css = f"#select2-{self.SELECT_ID}-results .select2-results__option"
        WebDriverWait(self.driver, 15).until(lambda _d: bool(self.select2_options(option_css)))
        self.wait_for_ajax_idle(timeout=5)
        options = self.select2_options(option_css)
        option = options[self.best_option_index(options, term)]
        ActionChains(self.driver).move_to_element(option).click().perform()
        self.wait_for_ajax_idle(timeout=5)

        shown = self.driver.find_element(By.ID, f"select2-{self.SELECT_ID}-container").text.lower()
        if not shown.strip() or "search for" in shown:
            raise SetupError(f"doc-type '{typed}' could not be selected for bulk upload")

    def selected_doc_type_id(self) -> str:
        return self.driver.find_element(By.ID, self.SELECT_ID).get_attribute("value") or ""

    def download_template(self, term: str) -> str:
        self.pick_bulk_doc_type(term)
        self.wait.until(
            lambda d: d.find_element(By.ID, "download_template_section").is_displayed()
            and d.find_element(By.ID, "download_template_section").get_attribute("innerHTML").strip()
        )
        self.wait_for_ajax_idle(timeout=4)
        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        for _ in range(2):
            started = time.time()
            buttons = self.visible("#download_template_section a, #download_template_section button, #download_template_section .btn")
            if buttons:
                self.click(buttons[0])
            else:
                self.click_label("download")
            file_name = self.wait_for_download(before, seconds=15, started=started)
            if file_name:
                return os.path.join(str(cfg.DOWNLOAD_DIR), file_name)
        raise SetupError("template was not downloaded")

    @staticmethod
    def template_header(path: str) -> list[str]:
        if not path.lower().endswith(".csv"):
            raise SetupError(f"the template is '{os.path.basename(path)}', this script reads CSV templates only")
        with open(path, newline="", encoding="utf-8-sig") as f:
            return next(csv.reader(f))

    @staticmethod
    def write_csv(path: str, header: list[str], rows: list[list[str]]) -> str:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def fetch_metadata_and_unique_values(self, doc_id: str) -> tuple[dict[str, dict], dict]:
        script = """
        var callback = arguments[arguments.length - 1];
        var docId = arguments[0];
        Promise.all([
            fetch('/api/v1/dms/categorization/metafield/?doc_id=' + docId).then(r => r.json()),
            fetch('/api/v1/dms/documents/metadata_value/?doc_id=' + docId).then(r => r.json())
        ]).then(([meta, unique_vals]) => {
            callback({meta: meta, unique_vals: unique_vals});
        }).catch(err => callback({error: err.toString()}));
        """
        self.driver.set_script_timeout(15)
        info = self.driver.execute_async_script(script, doc_id)
        fields = {f["title"].lower(): f for f in info.get("meta", [])}
        unique_vals = info.get("unique_vals", {})
        return fields, unique_vals

    def system_date_format(self) -> str:
        """Read date format shown by `#required_date_format` (`bulk_upload.js`) and map to strftime."""
        raw = ""
        els = self.driver.find_elements(By.ID, "required_date_format")
        if els:
            raw = (els[0].text or "").strip().upper()
        if raw.startswith("DD/MM"):
            return "%d/%m/%Y"
        if raw.startswith("YYYY-MM"):
            return "%Y-%m-%d"
        return "%m/%d/%Y"

    @staticmethod
    def ensure_min_size(path: str, min_mb: float = 1.1) -> str:
        sz = os.path.getsize(path)
        target_bytes = int(min_mb * 1024 * 1024)
        if sz >= target_bytes:
            return path
        ext = os.path.splitext(path)[1].lower()
        pad_len = target_bytes - sz
        if ext == ".pdf":
            with open(path, "ab") as f:
                f.write(b"\n%" + b"0" * pad_len)
        elif ext in (".txt", ".csv"):
            with open(path, "ab") as f:
                f.write(b"\n" + b"A" * pad_len)
        elif ext in (".docx", ".xlsx", ".pptx"):
            raise SetupError(f"cannot pad ZIP-based office file '{os.path.basename(path)}' safely; use a native >= 1MB sample")
        else:
            with open(path, "ab") as f:
                f.write(b"0" * pad_len)
        return path

    @staticmethod
    def build_valid_csv_row(
        header: list[str],
        number: int,
        path: str,
        run_id: str,
        meta_fields: dict[str, dict],
        used_unique: dict[str, set[str]],
        date_fmt: str = "%m/%d/%Y",
    ) -> list[str]:
        row = []
        for i, col in enumerate(header):
            clow = col.strip().lower()
            if "file" in clow:
                row.append(os.path.basename(path))
            elif clow == "status":
                row.append("")
            elif clow == "document_name":
                row.append(f"AUTO_BULK_{run_id}_{number}")
            elif clow in meta_fields:
                mf = meta_fields[clow]
                dtype = mf.get("data_type")
                is_unique = bool(mf.get("unique"))
                field_title = mf.get("title")

                if dtype == 1:
                    val = str(random.randint(100000, 999999))
                    while is_unique and val in used_unique.get(field_title, set()):
                        val = str(random.randint(100000, 999999))
                elif dtype == 5:
                    val = f"{random.randint(10000, 99999)}.{random.randint(10, 99)}"
                    while is_unique and val in used_unique.get(field_title, set()):
                        val = f"{random.randint(10000, 99999)}.{random.randint(10, 99)}"
                elif dtype == 3:
                    options = [line.strip() for line in (mf.get("default_text") or "").splitlines() if line.strip()] or ["A", "B", "C"]
                    val = options[0]
                    for _ in range(100):
                        k = min(len(options), random.randint(2, 5) if mf.get("multiselect") else 1)
                        cand = ",".join(sorted(random.sample(options, k)))
                        if not is_unique or cand not in used_unique.get(field_title, set()):
                            val = cand
                            break
                elif dtype == 4:
                    val = datetime.now().strftime(date_fmt)
                else:
                    mx = mf.get("max") or 20
                    val = f"AUTO_{run_id}_{number}"[:mx]
                    while is_unique and val in used_unique.get(field_title, set()):
                        val = f"A{random.randint(1000, 9999)}_{number}"[:mx]

                if is_unique and field_title:
                    used_unique.setdefault(field_title, set()).add(val)
                row.append(val)
            else:
                row.append(f"AUTO_{run_id}_{number}_{i}")
        return row

    @classmethod
    def build_duplicate_unique_rows(
        cls,
        header: list[str],
        path1: str,
        path2: str,
        run_id: str,
        meta_fields: dict[str, dict],
        used_unique: dict[str, set[str]],
        date_fmt: str = "%m/%d/%Y",
    ) -> list[list[str]]:
        """Build 2 otherwise valid CSV rows that collide ONLY on a unique metadata column."""
        row1 = cls.build_valid_csv_row(header, 0, path1, run_id, meta_fields, used_unique, date_fmt)
        row2 = cls.build_valid_csv_row(header, 1, path2, run_id, meta_fields, used_unique, date_fmt)
        unique_cols = [
            idx for idx, col in enumerate(header)
            if col.strip().lower() in meta_fields and meta_fields[col.strip().lower()].get("unique")
        ]
        if not unique_cols:
            unique_cols = [
                idx for idx, col in enumerate(header)
                if col.strip().lower() in meta_fields
            ][:1]
        if unique_cols:
            col_idx = unique_cols[0]
            row2[col_idx] = row1[col_idx]
        return [row1, row2]

    @classmethod
    def build_wrong_format_row(
        cls,
        header: list[str],
        path: str,
        run_id: str,
        meta_fields: dict[str, dict],
        used_unique: dict[str, set[str]],
        date_fmt: str = "%m/%d/%Y",
    ) -> list[str]:
        """Build a CSV row with invalid values in typed fields (int/float/dropdown/date)."""
        row = cls.build_valid_csv_row(header, 0, path, run_id, meta_fields, used_unique, date_fmt)
        for idx, col in enumerate(header):
            clow = col.strip().lower()
            if clow in meta_fields:
                dtype = meta_fields[clow].get("data_type")
                if dtype in (1, 3, 4, 5):
                    row[idx] = "!!bad_format!!"
        return row

    def parse_upload_report(self) -> dict:
        """Read rows in `#csv_file_data` and `#download_report` link (`bulk_upload.js`)."""
        def _cell_text(td) -> str:
            return (td.text or td.get_attribute("textContent") or "").strip()

        rows = []
        for tr in self.driver.find_elements(By.CSS_SELECTOR, "#csv_file_data tr"):
            tds = tr.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 4:
                rows.append({
                    "index": _cell_text(tds[0]),
                    "detail": _cell_text(tds[1]),
                    "status": _cell_text(tds[3]),
                })
        report_links = self.driver.find_elements(By.CSS_SELECTOR, "#download_report a")
        href = report_links[0].get_attribute("href") if report_links else ""
        return {
            "rows": rows,
            "has_report_link": bool(report_links and href),
            "report_href": href or "",
        }

    def _wait_csv_section_settled(self, timeout: int = 5) -> None:
        """Wait for jQuery slide/fade animation on `#csv_file_section` to finish."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda drv: drv.execute_script(
                    "var el = document.getElementById('csv_file_section');"
                    "if (!el) return true;"
                    "var st = window.getComputedStyle(el);"
                    "var animating = window.jQuery ? window.jQuery(el).is(':animated') : false;"
                    "return !animating && st.display !== 'none' && parseFloat(st.opacity || '1') >= 0.99;"
                )
            )
        except TimeoutException:
            pass

    def bulk_submit(self, term: str, csv_path: str, files: tuple[str, ...] | list[str] = ()) -> tuple[bool, str]:
        self.pick_bulk_doc_type(term)
        csv_input = self.driver.find_element(By.ID, "csv_file")
        self.driver.execute_script("arguments[0].style.display='block'; arguments[0].style.visibility='visible';", csv_input)

        def _section_shown(drv) -> bool:
            return drv.find_element(By.ID, "csv_file_section").is_displayed()

        try:
            csv_input.send_keys(csv_path)
            self.wait_for_ajax_idle(timeout=4)
            alert = self.alert_message()
            if alert:
                return False, f"alert: {alert}"
            WebDriverWait(self.driver, 10).until(lambda drv: _section_shown(drv) or bool(drv.find_elements(By.CSS_SELECTOR, "#csv_file_data tr")))
            self._wait_csv_section_settled()
        except UnexpectedAlertPresentException as error:
            return False, f"alert: {self.alert_message(error)}"
        except TimeoutException:
            return False, "the CSV file was not accepted and the page showed no message"

        if not _section_shown(self.driver):
            return False, self.popup_text() or "CSV section did not appear"

        folder = None
        try:
            if files:
                folder = tempfile.mkdtemp(prefix="AUTO_bulk_")
                for path in files:
                    shutil.copy(path, folder)
                self.driver.find_element(By.ID, "uploadable_files").send_keys(folder)
                self.wait_for_ajax_idle(timeout=5)

            self.click(self.driver.find_element(By.ID, "start_upload"))

            def _settled(_d) -> bool:
                alert_txt = self.alert_message()
                if alert_txt:
                    return True
                popup = self.popup_text()
                report = self.parse_upload_report()
                rows = report["rows"]
                if popup and "select a folder" in popup.lower():
                    if rows and not any(r["detail"] or r["status"] for r in rows):
                        return False
                    return True
                if not rows:
                    return False
                all_done = all(
                    r["status"].upper() == "SUCCESS"
                    or r["status"].upper() == "ERROR"
                    or r["status"].upper().startswith("FAILED:")
                    for r in rows
                )
                if not all_done:
                    return False
                if files and all(r["status"].upper() == "SUCCESS" for r in rows):
                    return report["has_report_link"]
                return True

            WebDriverWait(self.driver, 90, poll_frequency=0.5).until(_settled)
            self._wait_csv_section_settled()
        except UnexpectedAlertPresentException as error:
            return False, f"alert: {self.alert_message(error)}"
        except TimeoutException:
            return False, f"Bulk upload timed out ({self.parse_upload_report()})"
        finally:
            if folder:
                shutil.rmtree(folder, ignore_errors=True)

        report = self.parse_upload_report()
        rows = report["rows"]
        summary_rows = "; ".join(f"{r['index']}: {r['detail']} -> {r['status']}" for r in rows)
        all_ok = bool(rows) and all(r["status"].upper() == "SUCCESS" for r in rows)
        if files and all_ok and not report["has_report_link"]:
            return False, f"All rows uploaded but #download_report link missing ({summary_rows})"
        return all_ok, summary_rows + (" | Bulk upload report link ready" if report["has_report_link"] else "")
