"""Page Object for the Robo2mation Core, DMS and Workflow report screens."""
from __future__ import annotations

from pathlib import Path
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage


class ReportPage(BasePage):
    """Encapsulates interactions and assertions for Robo2mation report tables."""

    ACCESS_DENIED_WORDS = (
        "permission denied", "access denied", "not authorized", "not permitted",
        "you do not have permission", "you don't have permission", "insufficient permission",
    )
    DEFAULT_TABLE_SELECTORS = (
        "table.dataTable",
        ".dataTables_wrapper table",
        "table#report_table",
        "table.table",
        "main table",
        "table",
    )
    TABLE_BODY_ROW_LOCATOR = (By.CSS_SELECTOR, "tbody tr")
    TABLE_HEADER_CELL_LOCATOR = (By.CSS_SELECTOR, "thead th")
    TABLE_SEARCH_SELECTORS = (
        "input.search_in_table",
        "input[placeholder='Type and press enter']",
    )
    PAGE_SIZE_SELECTORS = (
        ".dataTables_length select",
        "select[name$='_length']",
    )
    EXPORT_ACTION_SELECTORS = {
        "copy": (".buttons-copy", "button[aria-label*='copy' i]", "a[title*='copy' i]"),
        "csv": (".buttons-csv", "button[aria-label*='csv' i]", "a[title*='csv' i]"),
        "excel": (".buttons-excel", "button[aria-label*='excel' i]", "a[title*='excel' i]"),
        "print": (".buttons-print", "button[aria-label*='print' i]", "a[title*='print' i]"),
        "download": ("button[title*='download' i]", "a[title*='download' i]", "button[aria-label*='download' i]"),
    }
    GENERIC_ACTION_LOCATOR = (By.CSS_SELECTOR, "button, a, input[type='button'], input[type='submit']")

    def __init__(self, driver, wait: WebDriverWait, table_selector: str = ""):
        super().__init__(driver, wait)
        self._table_selectors = (
            (table_selector.strip(),) + self.DEFAULT_TABLE_SELECTORS
            if table_selector and table_selector.strip()
            else self.DEFAULT_TABLE_SELECTORS
        )

    def open(self, base_url: str, route: str) -> None:
        self.driver.get(base_url.rstrip("/") + "/" + route.strip("/"))
        self.wait_for_page_load()

    def is_access_denied(self) -> bool:
        body = self.body_text().casefold()
        if any(word in body for word in self.ACCESS_DENIED_WORDS):
            return True
        current = self.driver.current_url.casefold()
        return "/login" in current and "report" not in current

    def report_table(self, timeout: int = 12):
        def find_table(_driver):
            # Sticky-header grids (e.g., DataTables / Ant Design) render header and body in
            # separate <table> elements. Only accept a table that actually has body rows.
            for selector in self._table_selectors:
                for table in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        if table.find_elements(*self.TABLE_BODY_ROW_LOCATOR):
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
            raise LookupError(f"Expected value for {description} is empty.")

        def expected_row_visible(_driver) -> bool:
            table = self.report_table(timeout=1)
            return bool(table and expected_text.casefold() in table.text.casefold())

        found = self.wait.until(expected_row_visible)
        if not found:
            raise AssertionError(f"Expected {description} '{expected_text}' was not found in the report rows.")

    def assert_table_not_contains(self, unexpected_text: str, description: str) -> None:
        if unexpected_text and unexpected_text.casefold() in self.table_text().casefold():
            raise AssertionError(f"Unexpected {description} '{unexpected_text}' was visible in a restricted report.")

    def _table_search_input(self):
        for selector in self.TABLE_SEARCH_SELECTORS:
            matches = self.visible_elements(By.CSS_SELECTOR, selector)
            if matches:
                return matches[0]
        return None

    def apply_label_filters(self, filters: dict[str, str], expected_text: str) -> None:
        if not filters:
            raise LookupError("No filter field values were provided for this test case.")
        if not expected_text:
            raise LookupError("Expected filter result text is empty.")

        # Prefer individual labeled form fields; fall back to the shared table search bar.
        try:
            fallback = None
            for label, value in filters.items():
                field = self.find_labeled_field(label)
                self.set_value(field, value)
                fallback = field
            self.apply_form(fallback)
        except LookupError:
            if self._table_search_input() is None:
                raise
            for label, value in filters.items():
                search_box = self._table_search_input()
                self.set_value(search_box, value)
                search_box.send_keys(Keys.ENTER)
                self.wait_for_ajax_idle()
                self.assert_table_contains(value, f"search result for '{label}'")

        self.assert_table_contains(expected_text, "filtered result")

    def apply_date_range(
        self,
        date_from: str,
        date_to: str,
        expected_text: str,
        from_selector: str = "input[type='date']:first-of-type",
        to_selector: str = "input[type='date']:last-of-type",
    ) -> None:
        if not date_from or not date_to:
            raise LookupError("Date range values (from/to) are required.")
        if not expected_text:
            raise LookupError("Expected date-filtered result text is empty.")
        from_fields = self.visible_elements(By.CSS_SELECTOR, from_selector)
        to_fields = self.visible_elements(By.CSS_SELECTOR, to_selector)
        if not from_fields or not to_fields:
            raise LookupError(
                "Date range fields were not found. Configure REPORT_DATE_FROM_SELECTOR and "
                "REPORT_DATE_TO_SELECTOR in report/.env.report."
            )
        self.set_value(from_fields[0], date_from)
        self.set_value(to_fields[0], date_to)
        self.apply_form(to_fields[0])
        self.wait_for_ajax_idle()
        self.assert_table_contains(expected_text, "date-filtered result")

    def sort_columns(self, labels: list[str]) -> None:
        table = self.report_table()
        if table is None:
            raise AssertionError("Cannot sort because the report table is missing.")
        headers = table.find_elements(*self.TABLE_HEADER_CELL_LOCATOR)
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
        for selector in self.PAGE_SIZE_SELECTORS:
            fields = self.visible_elements(By.CSS_SELECTOR, selector)
            if fields:
                select = Select(fields[0])
                if size.casefold() == "all":
                    option = next(
                        (o for o in select.options if "all" in o.text.casefold() or o.get_attribute("value") == "-1"),
                        None,
                    )
                    if option is None:
                        raise LookupError("The table has no 'All' page-size option.")
                    select.select_by_value(option.get_attribute("value"))
                else:
                    select.select_by_visible_text(size)
                return
        raise LookupError("The report page-size selector was not found.")

    def click_action(self, action: str):
        key = action.casefold()
        for selector in self.EXPORT_ACTION_SELECTORS.get(key, ()):
            matches = self.visible_elements(By.CSS_SELECTOR, selector)
            if matches:
                self.click(matches[0])
                return matches[0]
        # Some report screens nest export options inside a Download menu.
        if key in {"copy", "csv", "excel", "print"}:
            download_buttons = []
            for selector in self.EXPORT_ACTION_SELECTORS["download"]:
                download_buttons.extend(self.visible_elements(By.CSS_SELECTOR, selector))
            if download_buttons:
                self.click(download_buttons[0])
                for selector in self.EXPORT_ACTION_SELECTORS.get(key, ()):
                    matches = self.visible_elements(By.CSS_SELECTOR, selector)
                    if matches:
                        self.click(matches[0])
                        return matches[0]
        for element in self.driver.find_elements(*self.GENERIC_ACTION_LOCATOR):
            try:
                text = self.normalize(
                    element.text
                    or element.get_attribute("value")
                    or element.get_attribute("title")
                    or element.get_attribute("aria-label")
                    or ""
                )
                if element.is_displayed() and element.is_enabled() and key in text.split():
                    self.click(element)
                    return element
            except Exception:
                continue
        raise LookupError(f"The '{action}' export/download control was not found.")

    def wait_for_download(self, directory: Path, before: set[str], extension: str, timeout: int = 30) -> Path:
        def _download_ready(_driver):
            if list(directory.glob("*.crdownload")):
                return False
            candidates = [
                path for path in directory.glob(f"*{extension}")
                if path.is_file() and path.name not in before
            ]
            if not candidates:
                return False
            candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
            return candidates[0]

        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(_download_ready)
        except TimeoutException as exc:
            raise TimeoutError(
                f"No new {extension} report download appeared in {directory} within {timeout} seconds."
            ) from exc
