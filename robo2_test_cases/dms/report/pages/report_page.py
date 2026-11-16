"""Page Object for the Robo2mation Core, DMS and Workflow report screens."""
from __future__ import annotations

import os
from pathlib import Path
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class ReportPage(BasePage):
    ACCESS_DENIED_WORDS = (
        "permission denied", "access denied", "not authorized", "not permitted",
        "you do not have permission", "you don't have permission", "insufficient permission",
    )
    TABLE_SELECTORS = (
        os.getenv("REPORT_TABLE_SELECTOR", "").strip(),
        "table.dataTable", ".dataTables_wrapper table", "table#report_table",
        "table.table", "main table", "table",
    )

    def open(self, base_url: str, route: str) -> None:
        self.driver.get(base_url.rstrip("/") + "/" + route.strip("/"))
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def is_access_denied(self) -> bool:
        body = self.body_text().casefold()
        if any(word in body for word in self.ACCESS_DENIED_WORDS):
            return True
        current = self.driver.current_url.casefold()
        return "/login" in current and "report" not in current

    def report_table(self, timeout: int = 12):
        def find_table(_driver):
            # Ant Design (and other sticky-header grids) render the header and the body as
            # two separate <table> elements. Only accept a table that actually has body rows
            # so we never return the header-only table and miss the data.
            for selector in self.TABLE_SELECTORS:
                if not selector:
                    continue
                for table in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        if table.find_elements(By.CSS_SELECTOR, "tbody tr"):
                            return table
                    except Exception:
                        continue
            return False
        try:
            return WebDriverWait(self.driver, timeout).until(find_table)
        except TimeoutException:
            return None

    def assert_accessible(self) -> None:
        table = self.report_table()
        if self.is_access_denied() or table is None:
            raise AssertionError(
                f"Report page was not accessible. URL: {self.driver.current_url}; "
                f"page text: {self.body_text()[:400]}"
            )

    def assert_denied(self) -> None:
        # Wait briefly for an access-denied message or a redirect away from the report.
        try:
            WebDriverWait(self.driver, 8).until(lambda _d: self.is_access_denied())
        except TimeoutException as exc:
            raise AssertionError(
                "The page did not show an explicit access-denied message or redirect to login. "
                "A missing table alone is not enough to prove access was denied."
            ) from exc

    def table_text(self) -> str:
        table = self.report_table()
        if table is None:
            raise AssertionError("The report data table was not found.")
        return table.text

    def assert_table_contains(self, expected_text: str, description: str) -> None:
        if not expected_text:
            raise LookupError(f"Set the expected sentinel value for {description} in report/.env.report.")
        def expected_row_visible(_driver) -> bool:
            table = self.report_table(timeout=1)
            return bool(table and expected_text.casefold() in table.text.casefold())

        found = self.wait.until(expected_row_visible)
        if not found:
            raise AssertionError(f"Expected {description} '{expected_text}' was not found in the report rows.")

    def assert_table_not_contains(self, unexpected_text: str, description: str) -> None:
        if unexpected_text and unexpected_text.casefold() in self.table_text().casefold():
            raise AssertionError(f"Unexpected {description} '{unexpected_text}' was visible in a restricted report.")

    def apply_label_filters(self, labels: list[str], values: dict[str, str], expected_text: str) -> None:
        if not labels:
            raise LookupError("No filter field labels are mapped for this test case.")
        fallback = None
        for label in labels:
            value = values.get(label)
            if value is None:
                # Allow a case-insensitive key match from the JSON mapping.
                value = next((v for key, v in values.items() if self.normalize(key) == self.normalize(label)), None)
            if not value:
                raise LookupError(
                    f"Missing test value for filter '{label}'. Add it to REPORT_FILTER_VALUES_JSON in report/.env.report."
                )
            field = self.find_labeled_field(label)
            self.set_value(field, value)
            fallback = field
        self.apply_form(fallback)
        if not expected_text:
            raise LookupError("Set REPORT_EXPECTED_FILTER_TEXT to a known value expected in the filtered rows.")
        self.assert_table_contains(expected_text, "filtered result")

    def apply_date_range(self, date_from: str, date_to: str, expected_text: str) -> None:
        if not date_from or not date_to:
            raise LookupError("Set REPORT_DATE_FROM and REPORT_DATE_TO in report/.env.report.")
        from_selector = os.getenv("REPORT_DATE_FROM_SELECTOR", "input[type='date']:first-of-type").strip()
        to_selector = os.getenv("REPORT_DATE_TO_SELECTOR", "input[type='date']:last-of-type").strip()
        from_fields = self.visible_elements(By.CSS_SELECTOR, from_selector)
        to_fields = self.visible_elements(By.CSS_SELECTOR, to_selector)
        if not from_fields or not to_fields:
            raise LookupError(
                "Date range fields were not found. Set REPORT_DATE_FROM_SELECTOR and "
                "REPORT_DATE_TO_SELECTOR to the actual date input CSS selectors."
            )
        self.set_value(from_fields[0], date_from)
        self.set_value(to_fields[0], date_to)
        self.apply_form(to_fields[0])
        if not expected_text:
            raise LookupError("Set REPORT_EXPECTED_DATE_TEXT to a known row value within the selected date range.")
        self.assert_table_contains(expected_text, "date-filtered result")

    def sort_columns(self, labels: list[str]) -> None:
        table = self.report_table()
        if table is None:
            raise AssertionError("Cannot sort because the report table is missing.")
        headers = table.find_elements(By.CSS_SELECTOR, "thead th")
        if not headers:
            raise LookupError("The report table has no visible column headers.")
        targets = labels or [headers[0].text.strip()]
        for label in targets:
            wanted = self.normalize(label)
            if wanted == "any":
                target = next((h for h in headers if "sorting" in (h.get_attribute("class") or "").casefold()), headers[0])
            else:
                target = next((h for h in headers if wanted in self.normalize(h.text)), None)
            if target is None:
                raise LookupError(f"Sortable report column '{label}' was not found.")
            before = (target.get_attribute("class") or "") + "|" + (target.get_attribute("aria-sort") or "")
            self.click(target)
            self.wait.until(lambda _d: (
                (target.get_attribute("class") or "") + "|" + (target.get_attribute("aria-sort") or "")
            ) != before)

    def choose_page_size(self, size: str = "10") -> None:
        selectors = [".dataTables_length select", "select[name$='_length']"]
        for selector in selectors:
            fields = self.visible_elements(By.CSS_SELECTOR, selector)
            if fields:
                from selenium.webdriver.support.ui import Select
                select = Select(fields[0])
                if size.casefold() == "all":
                    option = next((o for o in select.options if "all" in o.text.casefold() or o.get_attribute("value") == "-1"), None)
                    if option is None:
                        raise LookupError("The table has no 'All' page-size option.")
                    select.select_by_value(option.get_attribute("value"))
                else:
                    select.select_by_visible_text(size)
                return
        raise LookupError("The report page-size selector was not found. Configure a page-size selector if this report uses a custom table.")

    def click_action(self, action: str):
        aliases = {
            "copy": [".buttons-copy", "button[aria-label*='copy' i]", "a[title*='copy' i]"],
            "csv": [".buttons-csv", "button[aria-label*='csv' i]", "a[title*='csv' i]"],
            "excel": [".buttons-excel", "button[aria-label*='excel' i]", "a[title*='excel' i]"],
            "print": [".buttons-print", "button[aria-label*='print' i]", "a[title*='print' i]"],
            "download": ["button[title*='download' i]", "a[title*='download' i]", "button[aria-label*='download' i]"],
        }
        key = action.casefold()
        for selector in aliases.get(key, []):
            matches = self.visible_elements(By.CSS_SELECTOR, selector)
            if matches:
                self.click(matches[0])
                return matches[0]
        # Some report screens put all export controls inside a Download menu.
        if key in {"copy", "csv", "excel", "print"}:
            download_buttons = []
            for selector in aliases["download"]:
                download_buttons.extend(self.visible_elements(By.CSS_SELECTOR, selector))
            if download_buttons:
                self.click(download_buttons[0])
                for selector in aliases.get(key, []):
                    matches = self.visible_elements(By.CSS_SELECTOR, selector)
                    if matches:
                        self.click(matches[0])
                        return matches[0]
        for element in self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='button'], input[type='submit']"):
            try:
                text = self.normalize(element.text or element.get_attribute("value") or element.get_attribute("title") or element.get_attribute("aria-label") or "")
                if element.is_displayed() and element.is_enabled() and key in text.split():
                    self.click(element)
                    return element
            except Exception:
                continue
        raise LookupError(f"The '{action}' export/download control was not found. Check the report's actual button selector.")

    def click_export_actions(self, actions: list[str], download_dir: Path) -> list[Path]:
        downloaded: list[Path] = []
        for action in actions:
            before = {p.name for p in download_dir.glob("*") if p.is_file()}
            if action.casefold() == "print":
                self.driver.execute_script("window.__reportPrintCalled=false; window.print=function(){window.__reportPrintCalled=true;};")
            self.click_action(action)
            if action.casefold() in {"csv", "excel"}:
                extension = ".csv" if action.casefold() == "csv" else ".xlsx"
                path = self.wait_for_download(download_dir, before, extension, timeout=25)
                downloaded.append(path)
            elif action.casefold() == "print":
                self.wait.until(lambda d: bool(d.execute_script("return window.__reportPrintCalled === true")))
            else:
                # Copy is validated by the control being clickable and the report remaining available.
                self.assert_accessible()
        return downloaded

    def wait_for_download(self, directory: Path, before: set[str], extension: str, timeout: int = 30) -> Path:
        deadline = time.time() + timeout
        while time.time() < deadline:
            candidates = [
                path for path in directory.glob(f"*{extension}")
                if path.is_file() and path.name not in before
            ]
            partials = list(directory.glob("*.crdownload"))
            if candidates and not partials:
                candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
                return candidates[0]
            time.sleep(0.5)
        raise TimeoutError(f"No new {extension} report download appeared in {directory} within {timeout} seconds.")
