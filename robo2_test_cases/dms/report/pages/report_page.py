"""Page Object for Robo2mation Core, DMS, and Workflow report screens."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import re
import time
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage


class ReportPage(BasePage):
    """Encapsulates UI interactions and assertions for Robo2mation report pages."""

    # --- Locators & Constants ---

    ACCESS_DENIED_WORDS = (
        "permission denied",
        "access denied",
        "not authorized",
        "unauthorized",
        "not permitted",
        "you do not have permission",
        "you don't have permission",
        "insufficient permission",
        "403 forbidden",
    )
    SERVER_ERROR_WORDS = (
        "500 internal server error",
        "server error (500)",
        "traceback (most recent call last)",
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
        "#filterToggle a, #filterToggle, .filter-toggler a, .filter-toggler",
    )
    FILTER_PANEL_LOCATOR = (By.CSS_SELECTOR, "#filterActionItems")
    SELECTPICKER_FILTER_SELECTOR = "#filterActionItems .bootstrap-select select.selectpicker"
    DATERANGE_INPUT_LOCATOR = (By.CSS_SELECTOR, "input[name='daterange'], input.date_input")
    DATERANGE_POPUP_LOCATOR = (By.CSS_SELECTOR, ".daterangepicker")
    DATERANGE_START_LOCATOR = (
        By.CSS_SELECTOR,
        ".daterangepicker input[name='daterangepicker_start']",
    )
    DATERANGE_END_LOCATOR = (
        By.CSS_SELECTOR,
        ".daterangepicker input[name='daterangepicker_end']",
    )
    DATERANGE_APPLY_LOCATOR = (By.CSS_SELECTOR, ".daterangepicker .applyBtn")
    DOC_TYPE_SELECT2_LOCATOR = (
        By.CSS_SELECTOR,
        "[aria-labelledby='select2-document_type-container']",
    )
    SELECT2_SEARCH_LOCATOR = (
        By.CSS_SELECTOR,
        "span.select2-container--open input.select2-search__field",
    )
    SELECT2_RESULTS_LOCATOR = (
        By.CSS_SELECTOR,
        ".select2-results__option:not(.loading-results):not(.select2-results__message)",
    )
    CUSTOM_REPORT_CARD_LOCATOR = (By.CSS_SELECTOR, "#grid_report .card")
    CUSTOM_REPORT_VIEW_LINK_LOCATOR = (By.CSS_SELECTOR, ".view-report a[href]")
    PAGE_SIZE_SELECTORS = (".dataTables_length select", "select[name$='_length']")
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
        "user": ("user", "users", "users name", "user name", "username", "initiator", "initiator name"),
        "all users": ("all users", "user", "users", "users name", "user name", "username"),
        "initiator name": ("initiator name", "initiator", "user", "users name", "created by"),
        "ip address": ("ip address", "source ip", "ip"),
        "source ip": ("source ip", "ip address", "ip"),
        "ip": ("ip", "ip address", "source ip"),
        "operation": ("operation", "operations", "action", "activity"),
        "all operation": ("all operation", "operation", "operations", "action", "activity"),
        "description": ("description", "details", "message", "remarks"),
        "project": ("project", "process", "project name", "process name", "workflow"),
        "process": ("process", "project", "process name", "project name", "workflow"),
        "app number": ("app number", "app id", "application id", "application number", "app no"),
        "status": ("status", "task status", "app status", "application status", "state"),
        "document name": ("document name", "document", "file name", "name"),
        "document type": ("document type", "doc type", "type"),
        "metafield": ("metafield", "meta field", "metadata", "meta"),
    }
    STANDARD_DOC_REPORT_HEADERS = frozenset({
        "uploader",
        "document name",
        "doc type",
        "document type",
        "upload time",
        "uploaded at",
        "ocr status",
        "archived at",
        "archived by",
        "action",
        "actions",
    })
    DATE_HEADER_KEYWORDS = (
        "date",
        "time",
        "created",
        "uploaded",
        "timestamp",
        "login",
        "archived",
    )

    def __init__(self, driver, wait: WebDriverWait, table_selector: str = ""):
        super().__init__(driver, wait)
        self._requested_route = ""
        self._table_selectors = (
            (table_selector.strip(),) + self.DEFAULT_TABLE_SELECTORS
            if table_selector and table_selector.strip()
            else self.DEFAULT_TABLE_SELECTORS
        )

    # =========================================================================
    # 1. Navigation & Access Checks
    # =========================================================================

    def open(self, base_url: str, route: str) -> None:
        self._requested_route = "/" + route.strip("/")
        self.driver.get(base_url.rstrip("/") + self._requested_route)
        self.wait_for_page_load()
        self.wait_for_ajax_idle()

    def open_custom_report(self, report_name: str = "") -> str:
        """Open a saved custom report card from the Custom Report grid page."""
        try:
            WebDriverWait(self.driver, 12).until(
                lambda _d: bool(
                    self.driver.find_elements(By.CSS_SELECTOR, "#grid_report .card .view-report a[href]")
                )
            )
        except TimeoutException as exc:
            raise LookupError("No custom report cards were found on the Custom Report page.") from exc

        cards = self.driver.find_elements(*self.CUSTOM_REPORT_CARD_LOCATOR)
        wanted = report_name.strip().casefold()

        candidates: list[tuple[str, str, str]] = []
        for card in cards:
            links = card.find_elements(*self.CUSTOM_REPORT_VIEW_LINK_LOCATOR)
            if not links:
                continue
            href = (links[0].get_attribute("href") or "").strip()
            if not href:
                continue
            titles = card.find_elements(By.CSS_SELECTOR, ".report-name")
            title = (titles[0].text or titles[0].get_attribute("title") or "").strip() if titles else ""
            candidates.append((href, title or "Custom Report", (card.text or "").strip()))

        if wanted:
            chosen = next(
                (c for c in candidates if c[1].casefold() == wanted),
                None,
            ) or next(
                (c for c in candidates if wanted in c[1].casefold() or wanted in c[2].casefold()),
                None,
            )
            if chosen is None:
                raise LookupError(f"Custom report '{report_name}' was not found on the Custom Report page.")
            to_try = [chosen]
        else:
            if not candidates:
                raise LookupError("No custom report card link was found on the Custom Report page.")
            to_try = candidates

        last_title = "Custom Report"
        for href, title, _card_text in to_try:
            last_title = title
            parsed_path = urlparse(href).path
            if parsed_path:
                self._requested_route = "/" + parsed_path.strip("/")
            self.driver.get(href)
            self.wait_for_page_load()
            self.wait_for_ajax_idle()
            if wanted:
                return title
            headers, _rows = self.read_table_data(max_rows=1)
            if headers:
                return title

        return last_title

    def is_access_denied(self) -> bool:
        body = self.body_text().casefold()
        title = (self.driver.title or "").casefold()
        if any(word in body or word in title for word in self.ACCESS_DENIED_WORDS):
            return True

        current = self.driver.current_url.casefold()
        if "/login" in current and "report" not in current:
            return True

        expected_slug = self._requested_route.strip("/").casefold()
        return bool(expected_slug and expected_slug not in current)

    def report_table(self, timeout: int = 20):
        def _find_table(_driver):
            # Prefer a visible table that already has tbody rows
            for selector in self._table_selectors:
                for table in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        if table.find_elements(*self.TABLE_BODY_ROW_LOCATOR):
                            return table
                    except StaleElementReferenceException:
                        continue
            # Fallback: accept an empty or slow-loading DataTables wrapper/table
            for selector in (".dataTables_wrapper", "table.dataTable", "table.table", "main table"):
                matches = self.visible_elements(By.CSS_SELECTOR, selector)
                if matches:
                    return matches[0]
            return False

        try:
            table = WebDriverWait(self.driver, timeout).until(_find_table)
            self.wait_for_ajax_idle(timeout=10)
            return table
        except TimeoutException:
            return None

    def report_chart(self, timeout: int = 5):
        """Locate a rendered chart (SVG/Canvas) on graphical reports."""
        chart_selectors = (
            ".card svg",
            ".card canvas",
            "#main svg",
            "#main canvas",
            ".highcharts-container",
            ".apexcharts-canvas",
        )

        def _find_chart(_driver):
            for selector in chart_selectors:
                for el in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        size = el.size or {}
                        if size.get("width", 0) > 100 and size.get("height", 0) > 100:
                            return el
                    except StaleElementReferenceException:
                        continue
            return False

        try:
            return WebDriverWait(self.driver, timeout).until(_find_chart)
        except TimeoutException:
            return None

    def assert_accessible(self) -> None:
        table = self.report_table(timeout=12)
        chart = None if table is not None else self.report_chart(timeout=8)
        current = self.driver.current_url.casefold()
        on_login = "/login" in current and "report" not in current
        has_rows = bool(table and table.find_elements(*self.TABLE_BODY_ROW_LOCATOR))

        if (
            (table is None and chart is None)
            or on_login
            or (not has_rows and chart is None and self.is_access_denied())
        ):
            raise AssertionError(
                f"Report page was not accessible. URL: {self.driver.current_url}; "
                f"page text: {self.body_text()[:300]}"
            )

    def assert_denied(self) -> None:
        body = self.body_text().casefold()
        if any(err in body for err in self.SERVER_ERROR_WORDS):
            raise AssertionError(
                f"Expected access-denied response, but page returned a server error at {self.driver.current_url}."
            )

        try:
            WebDriverWait(self.driver, 8).until(lambda _d: self.is_access_denied())
            return
        except TimeoutException:
            pass

        if self.is_access_denied():
            return

        if self.report_table(timeout=2) is None:
            return

        raise AssertionError(
            f"Expected access to be denied, but the report table was accessible at {self.driver.current_url}."
        )

    def assert_page_contains(self, expected_text: str, description: str = "element") -> None:
        if expected_text.casefold() not in self.body_text().casefold():
            raise AssertionError(f"Expected {description} '{expected_text}' was not visible on the page.")

    # =========================================================================
    # 2. Table Reading & Visibility Assertions
    # =========================================================================

    def read_table_data(self, max_rows: int = 50) -> tuple[list[str], list[list[str]]]:
        """Return (headers, rows) from the active report table (excludes empty placeholder rows)."""
        table = self.report_table(timeout=10)
        if table is None:
            return [], []

        data = self.driver.execute_script(
            "var tbl = arguments[0], limit = arguments[1];"
            "function leafHeaders(root) {"
            "  var trs = root ? root.querySelectorAll('thead tr') : [];"
            "  if (!trs.length) return [];"
            "  return Array.from(trs[trs.length - 1].querySelectorAll('th'))"
            "    .map(function(th) { return (th.textContent || '').trim(); });"
            "}"
            "var headers = leafHeaders(tbl);"
            "if (!headers.some(Boolean)) {"
            "  var wrap = tbl.closest('.dataTables_wrapper');"
            "  if (wrap) headers = leafHeaders(wrap.querySelector('.dataTables_scrollHead'));"
            "}"
            "var rows = [];"
            "var trs = tbl.querySelectorAll('tbody tr');"
            "for (var i = 0; i < trs.length && rows.length < limit; i++) {"
            "  if (trs[i].querySelector('td.dataTables_empty')) continue;"
            "  var cells = Array.from(trs[i].querySelectorAll('td'))"
            "    .map(function(td) { return (td.textContent || '').trim(); });"
            "  if (cells.length) rows.push(cells);"
            "}"
            "return {headers: headers, rows: rows};",
            table,
            max_rows,
        )
        if not data:
            return [], []
        return data.get("headers") or [], data.get("rows") or []

    def row_count(self) -> int:
        _headers, rows = self.read_table_data(max_rows=500)
        return len(rows)

    def assert_has_rows(self, context: str = "report") -> int:
        self.assert_accessible()
        count = self.row_count()
        if count == 0:
            raise AssertionError(f"Expected data rows for {context}, but the report table was empty.")
        return count

    def assert_headers_present(self, expected_columns: list[str]) -> None:
        headers, _rows = self.read_table_data(max_rows=1)
        norm_headers = [self.normalize(h) for h in headers if h]
        if not norm_headers:
            raise AssertionError("No table column headers were found on the report page.")

        missing = [
            col for col in expected_columns
            if not any(self.normalize(col) in h for h in norm_headers)
        ]
        if missing:
            raise AssertionError(
                f"Missing expected report columns: {missing}. Visible headers: {headers}"
            )

    def table_text(self) -> str:
        table = self.report_table(timeout=5)
        if table is not None:
            return table.text
        chart = self.report_chart(timeout=5)
        if chart is not None:
            return chart.text or self.body_text()
        raise AssertionError("The report data table was not found.")

    def assert_table_contains(
        self, expected_text: str, description: str, timeout: int | None = None
    ) -> None:
        if not expected_text:
            raise LookupError(f"Expected value for {description} is empty.")

        def _row_visible(_driver) -> bool:
            table = self.report_table(timeout=1)
            if table is not None:
                return expected_text.casefold() in table.text.casefold()
            chart = self.report_chart(timeout=1)
            if chart is not None:
                return expected_text.casefold() in (chart.text or self.body_text()).casefold()
            return False

        waiter = (
            WebDriverWait(self.driver, timeout, ignored_exceptions=(StaleElementReferenceException,))
            if timeout is not None
            else self.wait
        )
        try:
            found = waiter.until(_row_visible)
        except TimeoutException as exc:
            raise AssertionError(
                f"Expected {description} '{expected_text}' was not found in the report rows."
            ) from exc
        if not found:
            raise AssertionError(
                f"Expected {description} '{expected_text}' was not found in the report rows."
            )

    @staticmethod
    def _row_exposes_other_user(
        cells: list[str], unexpected_text: str, allow_with_text: str = ""
    ) -> bool:
        other_low = unexpected_text.strip().casefold()
        own_low = allow_with_text.strip().casefold()
        norm_cells = [c.casefold() for c in cells if c]
        if not other_low or not any(other_low in c for c in norm_cells):
            return False
        if not own_low:
            return True
        has_own_cell = any(
            f"({own_low})" in c or (own_low in c and other_low not in c)
            for c in norm_cells
        )
        return not has_own_cell

    def assert_table_not_contains(
        self, unexpected_text: str, description: str, allow_with_text: str = ""
    ) -> None:
        if not unexpected_text:
            return
        if allow_with_text:
            _headers, rows = self.read_table_data(max_rows=100)
            if rows:
                for cells in rows:
                    if self._row_exposes_other_user(cells, unexpected_text, allow_with_text):
                        raise AssertionError(
                            f"Unexpected {description} '{unexpected_text}' was visible in a restricted report."
                        )
                return

        if unexpected_text.casefold() in self.table_text().casefold():
            raise AssertionError(
                f"Unexpected {description} '{unexpected_text}' was visible in a restricted report."
            )

    def assert_has_other_user_record(self, own_username: str, max_rows: int = 100) -> str:
        """Verify at least one visible table row belongs to a user other than `own_username`."""
        self.assert_has_rows(f"other-user check (excluding '{own_username}')")
        table = self.report_table(timeout=10)
        if table is None:
            raise AssertionError("The report data table was not found.")

        data = self.driver.execute_script(
            "var tbl = arguments[0], limit = arguments[1];"
            "function leafHeaders(root) {"
            "  var trs = root ? root.querySelectorAll('thead tr') : [];"
            "  if (!trs.length) return [];"
            "  return Array.from(trs[trs.length - 1].querySelectorAll('th'))"
            "    .map(function(th) { return (th.textContent || '').trim(); });"
            "}"
            "var headers = leafHeaders(tbl);"
            "if (!headers.some(Boolean)) {"
            "  var wrap = tbl.closest('.dataTables_wrapper');"
            "  if (wrap) headers = leafHeaders(wrap.querySelector('.dataTables_scrollHead'));"
            "}"
            "var rows = [];"
            "var trs = tbl.querySelectorAll('tbody tr');"
            "for (var i = 0; i < trs.length && rows.length < limit; i++) {"
            "  if (trs[i].querySelector('td.dataTables_empty')) continue;"
            "  var cells = Array.from(trs[i].querySelectorAll('td'))"
            "    .map(function(td) { return (td.textContent || '').trim(); });"
            "  if (cells.length) rows.push(cells);"
            "}"
            "return {headers: headers, rows: rows};",
            table,
            max_rows,
        )
        headers = (data or {}).get("headers") or []
        rows = (data or {}).get("rows") or []
        if not rows:
            raise AssertionError("Expected report data rows, but the table was empty.")

        own_low = own_username.strip().casefold()
        user_header_keywords = (
            "user",
            "initiator",
            "participant",
            "uploader",
            "created by",
            "updated by",
            "owner",
        )
        user_cols = (
            [
                i for i, h in enumerate(headers)
                if any(kw in self.normalize(h) for kw in user_header_keywords)
            ]
            if len(headers) == len(rows[0])
            else []
        )
        placeholders = {"", "n/a", "-", "none", "null"}

        for row in rows:
            row_has_own = any(
                f"({own_low})" in (c or "").casefold()
                or (c or "").strip().casefold() == own_low
                for c in row
            )
            if row_has_own:
                continue

            if user_cols:
                for idx in user_cols:
                    if idx >= len(row):
                        continue
                    cell = " ".join((row[idx] or "").split()).strip()
                    if cell.casefold() in placeholders:
                        continue
                    match = re.search(r"\(([^()]+)\)", cell)
                    extracted = (match.group(1) if match else cell).strip().casefold()
                    if extracted and extracted not in placeholders and extracted != own_low:
                        return cell
            else:
                for raw in row:
                    cell = " ".join((raw or "").split()).strip()
                    match = re.search(r"\(([a-zA-Z0-9._-]+)\)", cell)
                    if match and match.group(1).strip().casefold() != own_low:
                        return cell

        raise AssertionError(
            f"No record belonging to a user other than '{own_username}' was found in the report rows."
        )

    # =========================================================================
    # 3. Dropdowns (Document Type Select2, User Selector, Selectpicker)
    # =========================================================================

    def select_document_type(self, doc_type: str) -> None:
        """Open the Select2 'Search for a document type' dropdown, search, and pick a match."""
        containers = self.visible_elements(*self.DOC_TYPE_SELECT2_LOCATOR)
        if not containers:
            raise LookupError("Document Type Select2 dropdown was not found on this report.")

        self.click(containers[0])
        if not self.visible_elements(*self.SELECT2_SEARCH_LOCATOR):
            # Select2 v4 sometimes requires jQuery .select2('open') or mousedown
            self.driver.execute_script(
                "if (window.jQuery && window.jQuery('#document_type').length) {"
                "  window.jQuery('#document_type').select2('open');"
                "} else {"
                "  arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));"
                "}",
                containers[0],
            )

        search_box = self.wait.until(
            lambda _d: (self.visible_elements(*self.SELECT2_SEARCH_LOCATOR) or [None])[0]
        )
        search_box.send_keys(doc_type)
        if not (search_box.get_attribute("value") or "").strip():
            self.driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));",
                search_box,
                doc_type,
            )

        def _matching_option(_driver):
            opts = [
                el for el in self.visible_elements(*self.SELECT2_RESULTS_LOCATOR)
                if (el.text or "").strip()
            ]
            if not opts:
                return False
            wanted = doc_type.strip().casefold()
            exact = next((o for o in opts if o.text.strip().casefold() == wanted), None)
            partial = next((o for o in opts if wanted in o.text.strip().casefold()), None)
            return exact or partial or opts[0]

        option = self.wait.until(_matching_option)
        self.driver.execute_script(
            "if (window.jQuery) { window.jQuery(arguments[0]).trigger('mouseup'); }"
            "else { arguments[0].dispatchEvent(new MouseEvent('mouseup', {bubbles: true})); }",
            option,
        )
        self.wait_for_ajax_idle()

    def user_dropdown_options_text(self) -> str:
        """Return concatenated text of all <select><option> items on the page."""
        return " ".join(
            (el.get_attribute("textContent") or "")
            for el in self.driver.find_elements(By.CSS_SELECTOR, "select option")
        ).casefold()

    def select_user_from_dropdown(self, username: str) -> str:
        """Select a user from the report's user <select> dropdown and return matched label."""
        wanted = username.strip().casefold()

        # 1. Try standard Selenium Select on visible user dropdowns first
        for select_el in self.driver.find_elements(By.CSS_SELECTOR, "select"):
            try:
                if select_el.find_elements(By.XPATH, "ancestor::*[contains(@class, 'dataTables_length')]"):
                    continue
                if select_el.is_displayed():
                    select = Select(select_el)
                    match = next(
                        (o for o in select.options if f"({wanted})" in o.text.casefold()),
                        None,
                    ) or next(
                        (o for o in select.options if wanted in o.text.casefold()),
                        None,
                    )
                    if match is not None:
                        select.select_by_visible_text(match.text)
                        self.wait_for_ajax_idle()
                        return match.text.strip()
            except StaleElementReferenceException:
                continue

        # 2. Fallback for styled/hidden <select> (Bootstrap Select / Select2)
        selected = self.driver.execute_script(
            "var wanted = arguments[0].toLowerCase();"
            "for (var s of document.querySelectorAll('select')) {"
            "  if (s.closest('.dataTables_length')) continue;"
            "  var opts = Array.from(s.options);"
            "  var match = opts.find(o => (o.textContent || '').toLowerCase().includes('(' + wanted + ')'))"
            "           || opts.find(o => (o.textContent || '').toLowerCase().includes(wanted));"
            "  if (match) {"
            "    s.value = match.value;"
            "    s.dispatchEvent(new Event('change', {bubbles: true}));"
            "    if (window.jQuery) window.jQuery(s).trigger('change');"
            "    return match.textContent.trim();"
            "  }"
            "}"
            "return null;",
            username,
        )
        if not selected:
            raise LookupError(f"User '{username}' was not found in the user filter dropdown.")
        self.wait_for_ajax_idle()
        return selected

    def _open_filter_panel(self) -> None:
        panels = self.driver.find_elements(*self.FILTER_PANEL_LOCATOR)
        if not panels:
            return
        panel = panels[0]
        classes = (panel.get_attribute("class") or "").split()
        visible_toggles = self.visible_elements(
            By.CSS_SELECTOR, "#filterActionItems .bootstrap-select button.dropdown-toggle"
        )
        if "close" not in classes and visible_toggles:
            return

        toggles = self.visible_elements(*self.FILTER_TOGGLE_LOCATOR)
        if not toggles:
            return
        self.click(toggles[0])
        try:
            WebDriverWait(self.driver, 5).until(
                lambda _d: "close" not in (panel.get_attribute("class") or "").split()
                or bool(
                    self.visible_elements(
                        By.CSS_SELECTOR,
                        "#filterActionItems .bootstrap-select button.dropdown-toggle",
                    )
                )
            )
        except TimeoutException:
            pass

    def _match_selectpicker_filters(
        self, filters: dict[str, str]
    ) -> list[tuple[object, str, str]] | None:
        selects = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTPICKER_FILTER_SELECTOR)
        if not selects:
            return None

        metadata = self.driver.execute_script(
            "return arguments[0].map(function(sel) {"
            "  var wrap = sel.closest('.bootstrap-select');"
            "  var btn = wrap ? wrap.querySelector('button.dropdown-toggle') : null;"
            "  var firstOpt = sel.options && sel.options.length ? sel.options[0].textContent : '';"
            "  return {id: sel.id || '', name: sel.name || '',"
            "          dataId: btn ? (btn.getAttribute('data-id') || '') : '',"
            "          title: btn ? (btn.getAttribute('title') || '') : '',"
            "          firstOpt: firstOpt || ''};"
            "});",
            selects,
        )

        descriptors = []
        for idx, (sel, meta) in enumerate(zip(selects, metadata or [])):
            raw = " ".join(str(meta.get(k) or "") for k in ("id", "name", "dataId", "title", "firstOpt"))
            desc = self.normalize(raw)
            descriptors.append((idx, sel, desc, set(desc.split())))

        used_indices: set[int] = set()
        matched = []
        for label, value in filters.items():
            wanted = self.normalize(label)
            terms = [wanted]
            if wanted.startswith("all "):
                terms.append(wanted[4:].strip())
            for term in list(terms):
                if term.endswith("s") and len(term) > 1:
                    terms.append(term[:-1])
            terms = [t for t in dict.fromkeys(terms) if t]

            best_score, best_entry = 0, None
            for entry in descriptors:
                idx, _sel, desc, words = entry
                if idx in used_indices:
                    continue
                score = 0
                for rank, term in enumerate(terms):
                    bonus = len(terms) - rank
                    if desc == term:
                        cand = 40 + bonus
                    elif f" {term} " in f" {desc} " or term in words:
                        cand = 30 + bonus
                    elif term in desc:
                        cand = 20 + bonus
                    else:
                        cand = 0
                    score = max(score, cand)
                if score > best_score:
                    best_score, best_entry = score, entry

            if best_entry is None:
                return None
            used_indices.add(best_entry[0])
            matched.append((best_entry[0], best_entry[1], label, value))

        matched.sort(key=lambda item: item[0])
        return [(sel, label, value) for _idx, sel, label, value in matched]

    def _select_selectpicker_option(self, select_el, label: str, value: str) -> str:
        chosen = self.driver.execute_script(
            "var sel = arguments[0], wanted = (arguments[1] || '').trim().toLowerCase();"
            "var allOpts = Array.from(sel.options || []).map(function(o, idx) {"
            "  return {index: idx, value: o.value, text: (o.textContent || '').trim()};"
            "});"
            "var opts = allOpts.filter(function(o) { return wanted === '' || o.value !== ''; });"
            "var match = opts.find(function(o) { return o.text.toLowerCase() === wanted; })"
            "  || opts.find(function(o) { return o.text.toLowerCase().indexOf('(' + wanted + ')') !== -1; })"
            "  || opts.find(function(o) { return o.text.toLowerCase().indexOf(wanted) !== -1; })"
            "  || opts.find(function(o) { return o.value.toLowerCase() === wanted; });"
            "if (!match) return null;"
            "match.duplicateValue = allOpts.filter(function(o) { return o.value === match.value; }).length > 1;"
            "return match;",
            select_el,
            value,
        )
        if not chosen:
            raise LookupError(f"Option '{value}' not found in '{label}' filter dropdown.")

        self.driver.execute_script(
            "var sel = arguments[0], val = arguments[1], optIndex = arguments[2], dup = arguments[3];"
            "if (dup) {"
            "  sel.selectedIndex = optIndex;"
            "  if (window.jQuery && window.jQuery.fn && window.jQuery.fn.selectpicker) {"
            "    window.jQuery(sel).selectpicker('render').trigger('change');"
            "  } else {"
            "    sel.dispatchEvent(new Event('change', {bubbles: true}));"
            "  }"
            "} else if (window.jQuery && window.jQuery.fn && window.jQuery.fn.selectpicker) {"
            "  window.jQuery(sel).selectpicker('val', val).trigger('change');"
            "} else {"
            "  sel.value = val;"
            "  sel.dispatchEvent(new Event('change', {bubbles: true}));"
            "  if (window.jQuery) window.jQuery(sel).trigger('change');"
            "}",
            select_el,
            chosen["value"],
            chosen["index"],
            bool(chosen.get("duplicateValue")),
        )
        self.wait_for_ajax_idle()
        return chosen["text"]

    # =========================================================================
    # 4. Search, Filter & Date Range
    # =========================================================================

    def _table_search_input(self):
        for selector in self.TABLE_SEARCH_SELECTORS:
            for elem in self.visible_elements(By.CSS_SELECTOR, selector):
                el_id = (elem.get_attribute("id") or "").casefold()
                placeholder = (elem.get_attribute("placeholder") or "").casefold()
                if el_id != "search_text" and "search documents" not in placeholder:
                    return elem
        return None

    def _clean_discovered_value(self, label: str, raw_text: str) -> str:
        text = " ".join(ln.strip() for ln in (raw_text or "").splitlines() if ln.strip()).strip()
        if not text or text.casefold() in {"n/a", "-", "none", "null"}:
            return ""
        wanted = self.normalize(label)
        if wanted in {"user", "users", "users name", "all users", "initiator name", "uploader"}:
            match = re.search(r"\(([^()]+)\)\s*$", text)
            return match.group(1).strip() if match else text
        if wanted in {"project", "process"}:
            return re.sub(r"\s*\([^)]*\)\s*$", "", text).strip() or text
        return text

    def discover_filter_values(self, labels: list[str]) -> dict[str, str]:
        """Read sample values from the loaded report table for dynamic fields (e.g. App Number)."""
        if not labels:
            return {}
        headers, rows = self.read_table_data(max_rows=25)
        if not headers or not rows:
            return {}

        norm_headers = [self.normalize(h) for h in headers]
        col_map: dict[str, int] = {}
        for label in labels:
            wanted = self.normalize(label)
            candidates = tuple(dict.fromkeys((wanted,) + self.HEADER_SYNONYMS.get(wanted, ())))
            col_idx = next(
                (i for term in candidates for i, h in enumerate(norm_headers) if h == term),
                None,
            )
            if col_idx is None:
                col_idx = next(
                    (i for term in candidates for i, h in enumerate(norm_headers) if term and term in h),
                    None,
                )
            if wanted == "metafield":
                meta_cols = [
                    i for term in candidates for i, h in enumerate(norm_headers)
                    if term and (h == term or term in h)
                ]
                fallback_cols = [
                    i for i, h in enumerate(norm_headers)
                    if h
                    and h not in self.STANDARD_DOC_REPORT_HEADERS
                    and i not in col_map.values()
                ]
                candidate_cols = list(dict.fromkeys(meta_cols + fallback_cols))
                col_idx = next(
                    (
                        i for i in candidate_cols
                        if any(
                            self._clean_discovered_value(label, row[i] if i < len(row) else "")
                            for row in rows
                        )
                    ),
                    col_idx,
                )
            if col_idx is not None:
                col_map[label] = col_idx

        if not col_map:
            return {}

        # Prefer a single row that has non-empty values for every requested column
        for row in rows:
            candidate_vals = {}
            for label, idx in col_map.items():
                cleaned = self._clean_discovered_value(label, row[idx] if idx < len(row) else "")
                if not cleaned:
                    candidate_vals = {}
                    break
                candidate_vals[label] = cleaned
            if candidate_vals:
                return candidate_vals

        # Otherwise collect first available value per column
        discovered: dict[str, str] = {}
        for label, idx in col_map.items():
            for row in rows:
                cleaned = self._clean_discovered_value(label, row[idx] if idx < len(row) else "")
                if cleaned:
                    discovered[label] = cleaned
                    break
        return discovered

    def apply_label_filters(self, filters: dict[str, str], expected_text: str = "") -> None:
        if not filters:
            raise LookupError("No filter field values were provided for this test case.")

        # Path 1: Bootstrap selectpicker filter panel (e.g. DMS Activity, KPI, Task Activity)
        selectpicker_matches = self._match_selectpicker_filters(filters)
        if selectpicker_matches is not None:
            all_selects = self.driver.find_elements(By.CSS_SELECTOR, self.SELECTPICKER_FILTER_SELECTOR)
            targets = [
                (
                    sel,
                    sel.get_attribute("id") or "",
                    all_selects.index(sel) if sel in all_selects else -1,
                    label,
                    value,
                )
                for sel, label, value in selectpicker_matches
            ]
            self._open_filter_panel()
            for sel, el_id, dom_pos, label, value in targets:
                target_el = sel
                try:
                    _ = target_el.tag_name
                except StaleElementReferenceException:
                    if el_id:
                        target_el = self.driver.find_element(By.ID, el_id)
                    else:
                        refreshed = self.driver.find_elements(
                            By.CSS_SELECTOR, self.SELECTPICKER_FILTER_SELECTOR
                        )
                        if 0 <= dom_pos < len(refreshed):
                            target_el = refreshed[dom_pos]
                self._select_selectpicker_option(target_el, label, value)
            verify_text = expected_text or list(filters.values())[-1]
            self.assert_table_contains(verify_text, "filtered result")
            return

        # Path 2: Dedicated labeled form inputs
        try:
            fallback_field = None
            for label, value in filters.items():
                field = self.find_labeled_field(label)
                self.set_value(field, value)
                fallback_field = field
            self.apply_form(fallback_field)
            self.wait_for_ajax_idle()
            verify_text = expected_text or list(filters.values())[-1]
            self.assert_table_contains(verify_text, "filtered result")
            return
        except LookupError:
            if self._table_search_input() is None:
                raise

        # Path 3: Single DataTable search input (search each configured label one by one)
        for label, value in filters.items():
            search_box = self._table_search_input()
            self.set_value(search_box, value)
            search_box.send_keys(Keys.ENTER)
            self.wait_for_ajax_idle()
            sp_fallback = self._match_selectpicker_filters({label: value})
            try:
                self.assert_table_contains(
                    value,
                    f"search result for '{label}'",
                    timeout=5 if sp_fallback else None,
                )
            except AssertionError:
                if not sp_fallback:
                    raise
                # Clear failed text query and apply the matching selectpicker filter instead
                search_box = self._table_search_input()
                if search_box is not None:
                    search_box.click()
                    search_box.send_keys(Keys.CONTROL, "a", Keys.BACKSPACE, Keys.ENTER)
                    self.wait_for_ajax_idle()
                self._open_filter_panel()
                sp_el, sp_label, sp_val = sp_fallback[0]
                self._select_selectpicker_option(sp_el, sp_label, sp_val)
                self.assert_table_contains(value, f"filter result for '{label}'")

        if expected_text:
            self.assert_table_contains(expected_text, "filtered result")

    @staticmethod
    def _parse_date(raw: str) -> datetime | None:
        text = (raw or "").strip()
        for fmt in ("%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_table_cell_date(cell_text: str) -> datetime | None:
        """Parse common Robo2mation table date formats (e.g. 'Nov 17th 2026', '2026-11-17')."""
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", cell_text or "", flags=re.IGNORECASE)

        patterns = (
            (r"\b([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})\b", ("%b %d %Y", "%b %d, %Y")),
            (r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b", ("%d-%b-%Y",)),
            (r"\b(\d{4}-\d{2}-\d{2})\b", ("%Y-%m-%d",)),
            (r"\b(\d{2}-\d{2}-\d{4})\b", ("%d-%m-%Y",)),
        )
        for pattern, formats in patterns:
            match = re.search(pattern, cleaned)
            if not match:
                continue
            token = match.group(1)
            for fmt in formats:
                try:
                    return datetime.strptime(token, fmt)
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
        try:
            WebDriverWait(self.driver, 5).until(
                lambda _d: self.visible_elements(*self.DATERANGE_POPUP_LOCATOR)
            )
        except TimeoutException:
            pass

        # If preset ranges (Today, Yesterday, Custom Range) are shown, click 'Custom Range'
        custom_ranges = [
            el
            for el in self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'daterangepicker')]//li[contains("
                "translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'custom')]",
            )
            if el.is_displayed()
        ]
        if custom_ranges:
            self.click(custom_ranges[0])
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda _d: self.visible_elements(*self.DATERANGE_START_LOCATOR)
                )
            except TimeoutException:
                pass

        start_els = self.visible_elements(*self.DATERANGE_START_LOCATOR)
        end_els = self.visible_elements(*self.DATERANGE_END_LOCATOR)
        if start_els and end_els:
            start_el, end_el = start_els[0], end_els[0]
            sample = start_el.get_attribute("value") or ""
            self.set_value(start_el, self._format_for_picker(date_from, sample))
            self.set_value(end_el, self._format_for_picker(date_to, sample))
            end_el.send_keys(Keys.TAB)
            apply_btns = self.visible_elements(*self.DATERANGE_APPLY_LOCATOR)
            if apply_btns:
                self.click(apply_btns[0])
            else:
                end_el.send_keys(Keys.ENTER)
            return

        # Fallback: set combined date string directly
        sample = picker_input.get_attribute("value") or ""
        sep = " - " if " - " in sample else (" to " if " to " in sample else " - ")
        first_part = sample.split(sep)[0].strip() if sep in sample else sample
        combined = (
            f"{self._format_for_picker(date_from, first_part)}"
            f"{sep}{self._format_for_picker(date_to, first_part)}"
        )
        self.driver.execute_script(
            "arguments[0].removeAttribute('readonly');"
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            picker_input,
            combined,
        )
        apply_btns = self.visible_elements(*self.DATERANGE_APPLY_LOCATOR)
        if apply_btns:
            self.click(apply_btns[0])
        else:
            picker_input.send_keys(Keys.ENTER)

    def _assert_table_dates_in_range(self, date_from: str, date_to: str) -> None:
        """If the report has a date column, verify every visible row falls inside [date_from, date_to]."""
        start_dt = self._parse_date(date_from)
        end_dt = self._parse_date(date_to)
        if not start_dt or not end_dt:
            return

        headers, rows = self.read_table_data(max_rows=25)
        if not headers or not rows:
            return

        date_col = next(
            (
                i for i, h in enumerate(headers)
                if any(kw in self.normalize(h) for kw in self.DATE_HEADER_KEYWORDS)
            ),
            None,
        )
        if date_col is None:
            return

        # Allow ±1 day tolerance for UTC vs local server timezone differences
        min_date = start_dt.date() - timedelta(days=1)
        max_date = end_dt.date() + timedelta(days=1)

        for row in rows:
            if date_col >= len(row):
                continue
            parsed = self._parse_table_cell_date(row[date_col])
            if parsed and not (min_date <= parsed.date() <= max_date):
                raise AssertionError(
                    f"Row date '{row[date_col]}' is outside the selected range ({date_from} to {date_to})."
                )

    def apply_date_range(
        self,
        date_from: str,
        date_to: str,
        expected_text: str = "",
        from_selector: str = "input[type='date']:first-of-type",
        to_selector: str = "input[type='date']:last-of-type",
    ) -> None:
        if not date_from or not date_to:
            raise LookupError("Date range values (from/to) are required.")

        from_fields = self.visible_elements(By.CSS_SELECTOR, from_selector)
        to_fields = self.visible_elements(By.CSS_SELECTOR, to_selector)

        if not (from_fields and to_fields):
            picker_inputs = self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
            if not picker_inputs:
                toggles = self.visible_elements(*self.FILTER_TOGGLE_LOCATOR)
                if toggles:
                    self.click(toggles[0])
                    try:
                        WebDriverWait(self.driver, 5).until(
                            lambda _d: self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
                            or self.visible_elements(By.CSS_SELECTOR, from_selector)
                        )
                    except TimeoutException:
                        pass
            from_fields = self.visible_elements(By.CSS_SELECTOR, from_selector)
            to_fields = self.visible_elements(By.CSS_SELECTOR, to_selector)
            picker_inputs = self.visible_elements(*self.DATERANGE_INPUT_LOCATOR)
        else:
            picker_inputs = []

        if from_fields and to_fields:
            self.set_value(from_fields[0], date_from)
            self.set_value(to_fields[0], date_to)
            self.apply_form(to_fields[0])
        elif picker_inputs:
            self._apply_daterangepicker(picker_inputs[0], date_from, date_to)
        else:
            raise LookupError("Date range input fields were not found on this report page.")

        self.wait_for_ajax_idle()
        if self.report_table(timeout=10) is None:
            raise AssertionError("Report table was not visible after applying the date range.")

        self._assert_table_dates_in_range(date_from, date_to)
        if expected_text and expected_text.strip() != "*":
            self.assert_table_contains(expected_text, "date-filtered result")

    # =========================================================================
    # 5. Sorting, Page Size & Export / Downloads
    # =========================================================================

    def sort_columns(self, labels: list[str]) -> None:
        table = self.report_table()
        if table is None:
            raise AssertionError("Cannot sort because the report table is missing.")

        headers = [
            h for h in table.find_elements(*self.TABLE_HEADER_CELL_LOCATOR)
            if h.is_displayed() and h.text.strip()
        ] or [
            h for h in self.visible_elements(*self.TABLE_HEADER_CELL_LOCATOR)
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
                    (h for h in headers if "sorting" in (h.get_attribute("class") or "").casefold()),
                    headers[0],
                )
            else:
                target = next(
                    (
                        h for h in headers
                        if any(
                            term == self.normalize(h.text) or term in self.normalize(h.text)
                            for term in candidates
                        )
                    ),
                    None,
                )

            if target is None:
                available = [h.text.strip() for h in headers]
                raise LookupError(
                    f"Sortable column '{label}' not found. Visible columns: {available}"
                )

            col_index = headers.index(target)
            _hdrs, rows_before = self.read_table_data(max_rows=10)
            col_before = [r[col_index] for r in rows_before if col_index < len(r)]
            header_before = (
                f"{target.get_attribute('class') or ''}|{target.get_attribute('aria-sort') or ''}"
            )

            self.click(target)
            self.wait_for_ajax_idle()

            def _sort_changed(_driver) -> bool:
                try:
                    header_now = (
                        f"{target.get_attribute('class') or ''}|{target.get_attribute('aria-sort') or ''}"
                    )
                    if header_now != header_before:
                        return True
                except StaleElementReferenceException:
                    return True
                _h, rows_now = self.read_table_data(max_rows=10)
                col_now = [r[col_index] for r in rows_now if col_index < len(r)]
                return bool(col_now and col_now != col_before)

            try:
                WebDriverWait(self.driver, 5).until(_sort_changed)
            except TimeoutException as exc:
                if len(set(col_before)) > 1:
                    raise AssertionError(
                        f"Clicking column header '{label}' did not trigger sorting or reorder rows."
                    ) from exc

    def choose_page_size(self, size: str = "10") -> None:
        custom_toggle_sel = ".dataTables_length .length_change > a, .length-option .dropdown > a"
        try:
            WebDriverWait(self.driver, 12).until(
                lambda _d: any(
                    self.visible_elements(By.CSS_SELECTOR, sel)
                    for sel in (*self.PAGE_SIZE_SELECTORS, custom_toggle_sel)
                )
            )
        except TimeoutException:
            pass

        # Standard DataTables <select>
        for selector in self.PAGE_SIZE_SELECTORS:
            fields = self.visible_elements(By.CSS_SELECTOR, selector)
            if fields:
                select = Select(fields[0])
                if size.casefold() == "all":
                    opt = next(
                        (
                            o for o in select.options
                            if "all" in o.text.casefold() or o.get_attribute("value") == "-1"
                        ),
                        None,
                    )
                    if opt is None:
                        raise LookupError("The table has no 'All' page-size option.")
                    select.select_by_value(opt.get_attribute("value"))
                else:
                    select.select_by_visible_text(size)
                self.wait_for_ajax_idle()
                return

        # Robo2mation custom Bootstrap length dropdown (.length_change)
        toggles = self.visible_elements(By.CSS_SELECTOR, custom_toggle_sel)
        if toggles:
            wanted = size.strip().casefold()
            current_els = self.visible_elements(
                By.CSS_SELECTOR, ".dataTables_length #current-length, .length-option #current-length"
            )
            if current_els and (current_els[0].text or "").strip().casefold() == wanted:
                return

            self.click(toggles[0])
            options = self.visible_elements(
                By.CSS_SELECTOR,
                ".dataTables_length .length_change .dropdown-menu a, .length-option .dropdown-menu a",
            )
            target = next(
                (
                    opt for opt in options
                    if (
                        wanted == "all"
                        and (
                            "all" in (opt.text or "").casefold()
                            or (opt.get_attribute("data-value") or "") == "-1"
                        )
                    )
                    or (opt.get_attribute("data-value") or "").strip().casefold() == wanted
                    or (opt.text or "").strip().casefold() == wanted
                ),
                None,
            )
            if target is None:
                available = [(opt.get_attribute("data-value") or opt.text).strip() for opt in options]
                raise LookupError(f"Page-size option '{size}' not found. Available: {available}")
            self.click(target)
            self.wait_for_ajax_idle()
            return

        raise LookupError("The report page-size selector was not found.")

    def select_first_row_if_selectable(self) -> None:
        table = self.report_table(timeout=5)
        if table is None:
            return
        checkboxes = table.find_elements(
            By.CSS_SELECTOR,
            "tbody input[type='checkbox'], tbody .ant-checkbox-input, tbody td.select-checkbox",
        )
        if not checkboxes:
            return
        if any(cb.is_selected() or "checked" in (cb.get_attribute("class") or "") for cb in checkboxes):
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
            except StaleElementReferenceException:
                continue
        return None

    def _dismiss_alerts(self) -> None:
        for close_btn in self.visible_elements(
            By.CSS_SELECTOR, "[data-notify] .close, .alert .close, button[data-dismiss='alert']"
        ):
            try:
                self.driver.execute_script("arguments[0].click();", close_btn)
            except Exception:
                pass

    def click_action(self, action: str):
        self.select_first_row_if_selectable()
        key = action.casefold()

        target = self._find_export_item(key)
        if target is not None:
            self.click(target)
            return target

        if key in {"copy", "csv", "excel", "print"}:
            triggers = []
            for selector in self.EXPORT_ACTION_SELECTORS["download"]:
                triggers.extend(self.visible_elements(By.CSS_SELECTOR, selector))

            if not triggers:
                triggers = [
                    el
                    for el in self.driver.find_elements(
                        By.XPATH,
                        "//input[contains(@placeholder, 'Type and press enter')]"
                        "/following::*[self::button or self::a or self::span[contains(@class, 'anticon')]]",
                    )
                    if el.is_displayed()
                ]

            for trigger in triggers:
                self._dismiss_alerts()
                try:
                    self.click(trigger)
                    target = WebDriverWait(self.driver, 3).until(
                        lambda _d: self._find_export_item(key) or False
                    )
                    if target:
                        self.click(target)
                        return target
                except Exception:
                    continue

        raise LookupError(f"The '{action}' export/download control was not found.")

    def wait_for_download(
        self,
        directory: Path,
        before: set[str],
        extension: str,
        timeout: int = 30,
        allow_queued: bool = False,
    ) -> Path | None:
        """
        Wait until a downloaded report file appears in `directory` (or OS Downloads).
        When `allow_queued=True`, returns None if the app shows a 'Requested Downloads' queue notice.
        """
        user_downloads = Path.home() / "Downloads"
        user_before = (
            {p.name for p in user_downloads.glob("*") if p.is_file()}
            if user_downloads.is_dir()
            else set()
        )
        valid_exts = {".csv"} if extension.lower() == ".csv" else {".xlsx", ".xls", ".csv", ".zip"}

        def _check_ready(_driver):
            in_progress = list(directory.glob("*.crdownload")) or list(directory.glob("*.tmp"))
            if not in_progress:
                candidates = [
                    p for p in directory.glob("*")
                    if p.is_file() and p.name not in before and p.suffix.lower() in valid_exts
                ]
                if candidates:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    return candidates[0]

                if user_downloads.is_dir():
                    sys_candidates = [
                        p for p in user_downloads.glob("*")
                        if p.is_file()
                        and p.name not in user_before
                        and not p.name.endswith((".crdownload", ".tmp"))
                        and p.suffix.lower() in valid_exts
                        and (time.time() - p.stat().st_mtime) < timeout + 5
                    ]
                    if sys_candidates:
                        sys_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                        return sys_candidates[0]

            if allow_queued:
                body_lower = self.body_text().casefold()
                if "requested_downloads" in body_lower or "requested downloads" in body_lower:
                    return "QUEUED"
            return False

        try:
            result = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(_check_ready)
            return None if result == "QUEUED" else result
        except TimeoutException as exc:
            raise TimeoutError(
                f"No new {extension} report download appeared in {directory} within {timeout} seconds."
            ) from exc
