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

    @staticmethod
    def ensure_min_size(path: str, min_mb: float = 1.1) -> str:
        sz = os.path.getsize(path)
        target_bytes = int(min_mb * 1024 * 1024)
        if sz < target_bytes:
            with open(path, "ab") as f:
                f.write(b"0" * (target_bytes - sz))
        return path

    @staticmethod
    def build_valid_csv_row(
        header: list[str],
        number: int,
        path: str,
        run_id: str,
        meta_fields: dict[str, dict],
        used_unique: dict[str, set[str]],
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
                    val = datetime.now().strftime("%m/%d/%Y")
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
            WebDriverWait(self.driver, 10).until(lambda drv: _section_shown(drv) or self.popup_text())
        except UnexpectedAlertPresentException as error:
            return False, f"alert: {self.alert_message(error)}"
        except TimeoutException:
            return False, "the CSV file was not accepted and the page showed no message"

        if not _section_shown(self.driver):
            return False, self.popup_text()

        folder = None
        try:
            if files:
                folder = tempfile.mkdtemp(prefix="AUTO_bulk_")
                for path in files:
                    shutil.copy(path, folder)
                self.driver.find_element(By.ID, "uploadable_files").send_keys(folder)
                self.wait_for_ajax_idle(timeout=5)
            try:
                ok, message = self.message_after(lambda: self.click(self.driver.find_element(By.ID, "start_upload")))
            except UnexpectedAlertPresentException as error:
                ok, message = False, f"alert: {self.alert_message(error)}"
            except TimeoutException:
                ok, message = False, self.popup_text()
        finally:
            if folder:
                shutil.rmtree(folder, ignore_errors=True)

        rows = " ".join(self.driver.find_element(By.ID, "csv_file_data").text.split())
        report = " ".join(self.driver.find_element(By.ID, "download_report").text.split())
        text = " | ".join(part for part in (message, rows, report) if part)
        if re.search(r"error|fail|invalid|already|required", text.lower()):
            ok = False
        return ok, text
