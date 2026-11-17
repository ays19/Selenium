"""Page Object for the Robo2mation Core, DMS and Workflow report screens."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage


class ReportPage(BasePage):
    """Encapsulates interactions and assertions for Robo2mation report tables."""

    ACCESS_DENIED_WORDS = (
        "permission denied",
        "access denied",
        "not authorized",
        "not permitted",
        "you do not have permission",
        "you don't have permission",
        "insufficient permission",
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
        "input[placeholder*='Type and press enter' i]",
        ".dataTables_filter input",
        "input[type='search']",
    )
    FILTER_TOGGLE_LOCATOR = (
        By.CSS_SELECTOR,
        "#filterToggle a, #filterToggle, button.filter-btn, [title*='Filter' i]",
    )
    DATERANGE_INPUT_LOCATOR = (
        By.CSS_SELECTOR,
        "input[name='daterange'], input.date_input",
    )
    DATERANGE_START_LOCATOR = (
        By.CSS_SELECTOR,
        ".daterangepicker input[name='daterangepicker_start']",
    )
    DATERANGE_END_LOCATOR = (
        By.CSS_SELECTOR,
        ".daterangepicker input[name='daterangepicker_end']",
    )
    DATERANGE_APPLY_LOCATOR = (By.CSS_SELECTOR, ".daterangepicker .applyBtn")
    PAGE_SIZE_SELECTORS = (
        ".dataTables_length select",
        "select[name$='_length']",
    )
    EXPORT_ACTION_SELECTORS: dict[str, tuple[str, ...]] = {
        "copy": (
            ".buttons-copy",
            "button[aria-label*='copy' i]",
            "a[title*='copy' i]",
            "[data-action*='copy' i]",
        ),
        "csv": (
            ".buttons-csv",
            "button[aria-label*='csv' i]",
            "a[title*='csv' i]",
            "a[href*='csv' i]",
            "[data-action*='csv' i]",
        ),
        "excel": (
            ".buttons-excel",
            "button[aria-label*='excel' i]",
            "a[title*='excel' i]",
            "a[href*='excel' i]",
            "a[href*='xlsx' i]",
            "[data-action*='excel' i]",
        ),
        "print": (
            ".buttons-print",
            "button[aria-label*='print' i]",
            "a[title*='print' i]",
            "[data-action*='print' i]",
        ),
        "download": (
            "button[title*='download' i]",
            "a[title*='download' i]",
            "button[aria-label*='download' i]",
            ".anticon-download",
            "i.fa-download",
            "i.zmdi-download",
            "#three-dot > li.dropdown > a",
        ),
    }
    GENERIC_ACTION_LOCATOR = (
        By.CSS_SELECTOR,
        ".ant-dropdown-menu-item, .dropdown-menu li, .dropdown-menu a, "
        ".dt-button-collection a, .dt-button-collection button, "
        "button, a, li[role='menuitem'], span.buttons-csv, span.buttons-excel, "
        "input[type='button'], input[type='submit']",
    )
    HEADER_SYNONYMS: dict[str, tuple[str, ...]] = {
        "users name": ("users name", "user name", "username", "user", "users"),
        "ip address": ("ip address", "source ip", "ip"),
        "operation": ("operation", "operations", "action", "activity"),
        "description": ("description", "details", "message", "remarks"),
    }

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
        self.wait_for_ajax_idle()

    def is_access_denied(self) -> bool:
        body = self.body_text().casefold()
        if any(word in body for word in self.ACCESS_DENIED_WORDS):
            return True
        current = self.driver.current_url.casefold()
        return "/login" in current and "report" not in current

    def report_table(self, timeout: int = 12):
        def find_table(_driver):
            # Sticky-header grids (e.g., DataTables / Ant Design) render header and body in
            # separate <table> elements. Prefer a table that actually has body rows.
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
            raise AssertionError(
                f"Expected {description} '{expected_text}' was not found in the report rows."
            )

    def assert_table_not_contains(self, unexpected_text: str, description: str) -> None:
        if unexpected_text and unexpected_text.casefold() in self.table_text().casefold():
            raise AssertionError(
                f"Unexpected {description} '{unexpected_text}' was visible in a restricted report."
            )

    def _table_search_input(self):
        for selector in self.TABLE_SEARCH_SELECTORS:
            for elem in self.visible_elements(By.CSS_SELECTOR, selector):
                el_id = (elem.get_attribute("id") or "").casefold()
                placeholder = (elem.get_attribute("placeholder") or "").casefold()
                if el_id != "search_text" and "search documents" not in placeholder:
                    return elem
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
            self.wait_for_ajax_idle()
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

    @staticmethod
    def _parse_date(raw: str) -> datetime | None:
        for fmt in ("%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw.strip(), fmt)
            except ValueError:
                continue
        return None

    def _format_for_picker(self, raw: str, sample_value: str) -> str:
        parsed = self._parse_date(raw)
        if parsed is None:
            return raw
        sample = (sample_value or "").strip()
        if "/" in sample:
            return parsed.strftime("%m/%d/%Y")
        if "-" in sample:
            parts = sample.split("-")
            if len(parts[0]) == 4:
                return parsed.strftime("%Y-%m-%d")
            return parsed.strftime("%d-%m-%Y" if len(parts[-1]) == 4 else "%d-%m-%y")
        return raw

    def _apply_daterangepicker(self, picker_input, date_from: str, date_to: str) -> None:
        self.click(picker_input)
        start_el = self.wait.until(
            EC.visibility_of_element_located(self.DATERANGE_START_LOCATOR)
        )
        end_el = self.wait.until(
            EC.visibility_of_element_located(self.DATERANGE_END_LOCATOR)
        )
        sample = start_el.get_attribute("value") or ""
        start_str = self._format_for_picker(date_from, sample)
        end_str = self._format_for_picker(date_to, sample)
        self.set_value(start_el, start_str)
        self.set_value(end_el, end_str)
        end_el.send_keys(Keys.TAB)
        apply_btns = self.visible_elements(*self.DATERANGE_APPLY_LOCATOR)
        if apply_btns:
            self.click(apply_btns[0])
        else:
            end_el.send_keys(Keys.ENTER)

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
        if from_fields and to_fields:
            self.set_value(from_fields[0], date_from)
            self.set_value(to_fields[0], date_to)
            self.apply_form(to_fields[0])
        else:
            picker_inputs = self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
            if not picker_inputs:
                toggles = self.visible_elements(*self.FILTER_TOGGLE_LOCATOR)
                if toggles:
                    self.click(toggles[0])
                    self.wait.until(
                        lambda _d: self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
                        or self.visible_elements(By.CSS_SELECTOR, from_selector)
                    )
            from_fields = self.visible_elements(By.CSS_SELECTOR, from_selector)
            to_fields = self.visible_elements(By.CSS_SELECTOR, to_selector)
            picker_inputs = self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
            if from_fields and to_fields:
                self.set_value(from_fields[0], date_from)
                self.set_value(to_fields[0], date_to)
                self.apply_form(to_fields[0])
            elif picker_inputs:
                self._apply_daterangepicker(picker_inputs[0], date_from, date_to)
            else:
                raise LookupError(
                    "Date range fields were not found. Configure REPORT_DATE_FROM_SELECTOR and "
                    "REPORT_DATE_TO_SELECTOR in report/.env.report."
                )

        self.wait_for_ajax_idle()
        self.assert_table_contains(expected_text, "date-filtered result")

    def sort_columns(self, labels: list[str]) -> None:
        table = self.report_table()
        if table is None:
            raise AssertionError("Cannot sort because the report table is missing.")

        # Collect visible headers from both the table and any sticky-header wrapper table
        headers = [
            h
            for h in table.find_elements(*self.TABLE_HEADER_CELL_LOCATOR)
            if h.is_displayed() and h.text.strip()
        ]
        if not headers:
            headers = [
                h
                for h in self.visible_elements(*self.TABLE_HEADER_CELL_LOCATOR)
                if h.text.strip()
            ]
        if not headers:
            raise LookupError("The report table has no visible column headers.")

        targets = labels or [headers[0].text.strip()]
        for label in targets:
            wanted = self.normalize(label)
            candidates = (wanted,) + self.HEADER_SYNONYMS.get(wanted, ())

            if wanted == "any":
                target = next(
                    (
                        h
                        for h in headers
                        if "sorting" in (h.get_attribute("class") or "").casefold()
                    ),
                    headers[0],
                )
            else:
                target = next(
                    (
                        h
                        for h in headers
                        if any(
                            term == self.normalize(h.text)
                            or term in self.normalize(h.text)
                            for term in candidates
                        )
                    ),
                    None,
                )

            if target is None:
                available = [h.text.strip() for h in headers]
                raise LookupError(
                    f"Sortable report column '{label}' was not found. Visible columns: {available}"
                )

            before = (
                (target.get_attribute("class") or "")
                + "|"
                + (target.get_attribute("aria-sort") or "")
            )
            self.click(target)
            self.wait_for_ajax_idle()
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda _d: (
                        (target.get_attribute("class") or "")
                        + "|"
                        + (target.get_attribute("aria-sort") or "")
                    )
                    != before
                )
            except TimeoutException:
                pass

    def choose_page_size(self, size: str = "10") -> None:
        for selector in self.PAGE_SIZE_SELECTORS:
            fields = self.visible_elements(By.CSS_SELECTOR, selector)
            if fields:
                select = Select(fields[0])
                if size.casefold() == "all":
                    option = next(
                        (
                            o
                            for o in select.options
                            if "all" in o.text.casefold()
                            or o.get_attribute("value") == "-1"
                        ),
                        None,
                    )
                    if option is None:
                        raise LookupError("The table has no 'All' page-size option.")
                    select.select_by_value(option.get_attribute("value"))
                else:
                    select.select_by_visible_text(size)
                self.wait_for_ajax_idle()
                return
        raise LookupError("The report page-size selector was not found.")

    def select_first_row_if_selectable(self) -> None:
        """If the report table has row selection checkboxes and none are checked, select the first row."""
        table = self.report_table(timeout=5)
        if table is None:
            return
        checkboxes = table.find_elements(
            By.CSS_SELECTOR,
            "tbody input[type='checkbox'], tbody .ant-checkbox-input, tbody td.select-checkbox",
        )
        if not checkboxes:
            return
        for cb in checkboxes:
            if cb.is_selected() or "checked" in (cb.get_attribute("class") or ""):
                return
        target = checkboxes[0]
        try:
            if target.is_displayed():
                self.click(target)
            else:
                wrapper = target.find_element(
                    By.XPATH, "./ancestor::*[self::label or self::td or self::span][1]"
                )
                self.click(wrapper)
            time.sleep(0.3)
        except Exception:
            pass

    def _find_export_item(self, key: str):
        for selector in self.EXPORT_ACTION_SELECTORS.get(key, ()):
            matches = self.visible_elements(By.CSS_SELECTOR, selector)
            if matches:
                return matches[0]

        for element in self.driver.find_elements(*self.GENERIC_ACTION_LOCATOR):
            try:
                if not element.is_displayed():
                    continue
                text = self.normalize(
                    element.text
                    or element.get_attribute("value")
                    or element.get_attribute("title")
                    or element.get_attribute("aria-label")
                    or element.get_attribute("data-original-title")
                    or ""
                )
                if key == text or key in text.split():
                    return element
            except Exception:
                continue
        return None

    def click_action(self, action: str):
        self.select_first_row_if_selectable()
        key = action.casefold()

        # 1. Click directly if the export button is already visible
        target = self._find_export_item(key)
        if target is not None:
            self.click(target)
            time.sleep(0.4)
            return target

        # 2. Otherwise open the Download dropdown menu first, then click the item
        if key in {"copy", "csv", "excel", "print"}:
            download_triggers = []
            for selector in self.EXPORT_ACTION_SELECTORS["download"]:
                download_triggers.extend(self.visible_elements(By.CSS_SELECTOR, selector))

            if not download_triggers:
                download_triggers = [
                    el
                    for el in self.driver.find_elements(
                        By.XPATH,
                        "//input[contains(@placeholder, 'Type and press enter')]/following::*[self::button or self::a or self::span[contains(@class, 'anticon')]]",
                    )
                    if el.is_displayed()
                ]

            for trigger in download_triggers:
                try:
                    self.click(trigger)
                    time.sleep(0.6)
                    target = self._find_export_item(key)
                    if target is not None:
                        self.click(target)
                        time.sleep(0.4)
                        return target
                except Exception:
                    continue

        raise LookupError(f"The '{action}' export/download control was not found.")

    def wait_for_download(
        self, directory: Path, before: set[str], extension: str, timeout: int = 30
    ) -> Path:
        user_downloads = Path.home() / "Downloads"
        user_before = (
            {p.name for p in user_downloads.glob("*") if p.is_file()}
            if user_downloads.is_dir()
            else set()
        )
        valid_exts = (
            {".csv"}
            if extension.lower() == ".csv"
            else {".xlsx", ".xls", ".csv", ".zip"}
        )

        def _download_ready(_driver):
            if list(directory.glob("*.crdownload")) or list(directory.glob("*.tmp")):
                return False
            candidates = [
                path
                for path in directory.glob("*")
                if path.is_file()
                and path.name not in before
                and path.suffix.lower() in valid_exts
            ]
            if candidates:
                candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
                return candidates[0]

            if user_downloads.is_dir():
                sys_candidates = [
                    path
                    for path in user_downloads.glob("*")
                    if path.is_file()
                    and path.name not in user_before
                    and not path.name.endswith((".crdownload", ".tmp"))
                    and path.suffix.lower() in valid_exts
                    and (time.time() - path.stat().st_mtime) < timeout + 5
                ]
                if sys_candidates:
                    sys_candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
                    return sys_candidates[0]
            return False

        try:
            return WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                _download_ready
            )
        except TimeoutException as exc:
            raise TimeoutError(
                f"No new {extension} report download appeared in {directory} within {timeout} seconds."
            ) from exc

    def wait_for_download_or_queued(
        self,
        directory: Path,
        before: set[str],
        extension: str,
        timeout: int = 30,
    ) -> Path | None:
        """Wait for a direct file download, or return None if the server queues it to Requested Downloads."""
        user_downloads = Path.home() / "Downloads"
        user_before = (
            {p.name for p in user_downloads.glob("*") if p.is_file()}
            if user_downloads.is_dir()
            else set()
        )
        valid_exts = (
            {".csv"}
            if extension.lower() == ".csv"
            else {".xlsx", ".xls", ".csv", ".zip"}
        )

        def _ready(_driver):
            if not list(directory.glob("*.crdownload")) and not list(
                directory.glob("*.tmp")
            ):
                candidates = [
                    path
                    for path in directory.glob("*")
                    if path.is_file()
                    and path.name not in before
                    and path.suffix.lower() in valid_exts
                ]
                if candidates:
                    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
                    return candidates[0]

                if user_downloads.is_dir():
                    sys_candidates = [
                        path
                        for path in user_downloads.glob("*")
                        if path.is_file()
                        and path.name not in user_before
                        and not path.name.endswith((".crdownload", ".tmp"))
                        and path.suffix.lower() in valid_exts
                        and (time.time() - path.stat().st_mtime) < timeout + 5
                    ]
                    if sys_candidates:
                        sys_candidates.sort(
                            key=lambda item: item.stat().st_mtime, reverse=True
                        )
                        return sys_candidates[0]

            body_lower = self.body_text().casefold()
            if (
                "requested_downloads" in body_lower
                or "requested downloads" in body_lower
            ):
                return "QUEUED"
            return False

        try:
            result = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(_ready)
            return None if result == "QUEUED" else result
        except TimeoutException as exc:
            raise TimeoutError(
                f"No new {extension} report download appeared in {directory} within {timeout} seconds."
            ) from exc