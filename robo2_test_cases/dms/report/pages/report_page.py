"""Page Object for the Robo2mation Core, DMS and Workflow report screens."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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
        "unauthorized",
        "not permitted",
        "you do not have permission",
        "you don't have permission",
        "insufficient permission",
        "403 forbidden",
        "404 not found",
        "page not found",
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
        self._requested_route = ""
        self._table_selectors = (
            (table_selector.strip(),) + self.DEFAULT_TABLE_SELECTORS
            if table_selector and table_selector.strip()
            else self.DEFAULT_TABLE_SELECTORS
        )

    def open(self, base_url: str, route: str) -> None:
        self._requested_route = "/" + route.strip("/")
        self.driver.get(base_url.rstrip("/") + self._requested_route)
        self.wait_for_page_load()
        self.wait_for_ajax_idle()

    def is_access_denied(self) -> bool:
        body = self.body_text().casefold()
        title = (self.driver.title or "").casefold()
        if any(word in body or word in title for word in self.ACCESS_DENIED_WORDS):
            return True

        current = self.driver.current_url.casefold()
        if "/login" in current and "report" not in current:
            return True

        expected_slug = getattr(self, "_requested_route", "").strip("/").casefold()
        if expected_slug and expected_slug not in current:
            return True

        return False

    def report_table(self, timeout: int = 20):
        def find_table(_driver):
            # 1. Prefer a visible table that has tbody rows
            for selector in self._table_selectors:
                for table in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        if table.find_elements(*self.TABLE_BODY_ROW_LOCATOR):
                            return table
                    except Exception:
                        continue
            # 2. Fallback: accept a visible DataTable container or table with thead headers
            #    (handles empty tables or slow AJAX tables that render headers first)
            for selector in (".dataTables_wrapper", "table.dataTable", "table.table", "main table"):
                matches = self.visible_elements(By.CSS_SELECTOR, selector)
                if matches:
                    return matches[0]
            return False

        try:
            table = WebDriverWait(self.driver, timeout).until(find_table)
            self.wait_for_ajax_idle(timeout=10)
            return table
        except TimeoutException:
            return None

    def report_chart(self, timeout: int = 5):
        """Locate a rendered chart (SVG/Canvas) on graphical report screens."""
        def find_chart(_driver):
            for selector in (
                ".card svg",
                ".card canvas",
                "#main svg",
                "#main canvas",
                ".highcharts-container",
                ".apexcharts-canvas",
            ):
                for el in self.visible_elements(By.CSS_SELECTOR, selector):
                    try:
                        size = el.size or {}
                        if size.get("width", 0) > 100 and size.get("height", 0) > 100:
                            return el
                    except Exception:
                        continue
            return False

        try:
            return WebDriverWait(self.driver, timeout).until(find_chart)
        except TimeoutException:
            return None

    def assert_accessible(self) -> None:
        table = self.report_table(timeout=12)
        chart = None if table is not None else self.report_chart(timeout=8)
        current = self.driver.current_url.casefold()
        on_login = "/login" in current and "report" not in current
        has_rows = bool(table and table.find_elements(*self.TABLE_BODY_ROW_LOCATOR))
        # A populated report table or rendered chart proves access even if log rows contain words like "unauthorized".
        if (table is None and chart is None) or on_login or (not has_rows and chart is None and self.is_access_denied()):
            raise AssertionError(
                f"Report page was not accessible. URL: {self.driver.current_url}; "
                f"page text: {self.body_text()[:400]}"
            )

    def assert_denied(self) -> None:
        try:
            WebDriverWait(self.driver, 8).until(
                lambda _d: self.is_access_denied() or self.report_table(timeout=1) is None
            )
        except TimeoutException:
            pass

        if self.is_access_denied():
            return

        if self.report_table(timeout=2) is None:
            return

        raise AssertionError(
            f"Expected access to be denied, but the report table was accessible at {self.driver.current_url}."
        )

    def table_text(self) -> str:
        table = self.report_table(timeout=5)
        if table is not None:
            return table.text
        chart = self.report_chart(timeout=5)
        if chart is not None:
            return chart.text or self.body_text()
        raise AssertionError("The report data table was not found.")

    def assert_table_contains(self, expected_text: str, description: str) -> None:
        if not expected_text:
            raise LookupError(f"Expected value for {description} is empty.")

        def expected_row_visible(_driver) -> bool:
            table = self.report_table(timeout=1)
            if table is not None:
                return expected_text.casefold() in table.text.casefold()
            chart = self.report_chart(timeout=1)
            if chart is not None:
                return expected_text.casefold() in (chart.text or self.body_text()).casefold()
            return False

        try:
            found = self.wait.until(expected_row_visible)
        except TimeoutException as exc:
            raise AssertionError(
                f"Expected {description} '{expected_text}' was not found in the report rows."
            ) from exc
        if not found:
            raise AssertionError(
                f"Expected {description} '{expected_text}' was not found in the report rows."
            )

    def assert_table_not_contains(self, unexpected_text: str, description: str) -> None:
        if unexpected_text and unexpected_text.casefold() in self.table_text().casefold():
            raise AssertionError(
                f"Unexpected {description} '{unexpected_text}' was visible in a restricted report."
            )

    def select_document_type(self, doc_type: str) -> None:
        """Open the Select2 'Search for a document type' dropdown, search, and pick a match."""
        containers = self.visible_elements(*self.DOC_TYPE_SELECT2_LOCATOR)
        if not containers:
            raise LookupError("Document Type Select2 dropdown was not found on this report.")
        self.click(containers[0])
        if not self.visible_elements(*self.SELECT2_SEARCH_LOCATOR):
            # Select2 v4 often listens for mousedown or jQuery .select2('open')
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

    def _table_search_input(self):
        for selector in self.TABLE_SEARCH_SELECTORS:
            for elem in self.visible_elements(By.CSS_SELECTOR, selector):
                el_id = (elem.get_attribute("id") or "").casefold()
                placeholder = (elem.get_attribute("placeholder") or "").casefold()
                if el_id != "search_text" and "search documents" not in placeholder:
                    return elem
        return None

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
        selects = self.driver.find_elements(
            By.CSS_SELECTOR, self.SELECTPICKER_FILTER_SELECTOR
        )
        if not selects:
            return None

        metadata = self.driver.execute_script(
            "return arguments[0].map(function(sel) {"
            "  var wrap = sel.closest('.bootstrap-select');"
            "  var btn = wrap ? wrap.querySelector('button.dropdown-toggle') : null;"
            "  var firstOpt = sel.options && sel.options.length ? sel.options[0].textContent : '';"
            "  return {"
            "    id: sel.id || '',"
            "    name: sel.name || '',"
            "    dataId: btn ? (btn.getAttribute('data-id') || '') : '',"
            "    title: btn ? (btn.getAttribute('title') || '') : '',"
            "    firstOpt: firstOpt || ''"
            "  };"
            "});",
            selects,
        )

        descriptors: list[tuple[int, object, str, set[str]]] = []
        for idx, (sel, meta) in enumerate(zip(selects, metadata or [])):
            raw = " ".join(
                str(meta.get(k) or "")
                for k in ("id", "name", "dataId", "title", "firstOpt")
            )
            desc = self.normalize(raw)
            descriptors.append((idx, sel, desc, set(desc.split())))

        used_indices: set[int] = set()
        matched: list[tuple[int, object, str, str]] = []

        for label, value in filters.items():
            wanted = self.normalize(label)
            terms = [wanted]
            if wanted.startswith("all "):
                terms.append(wanted[4:].strip())
            for term in list(terms):
                if term.endswith("s") and len(term) > 1:
                    terms.append(term[:-1])
            terms = [t for t in dict.fromkeys(terms) if t]

            best_score = 0
            best_entry = None
            for entry in descriptors:
                idx, _sel, desc, words = entry
                if idx in used_indices:
                    continue
                score = 0
                for term_rank, term in enumerate(terms):
                    term_bonus = len(terms) - term_rank
                    if desc == term:
                        cand_score = 40 + term_bonus
                    elif f" {term} " in f" {desc} " or term in words:
                        cand_score = 30 + term_bonus
                    elif term in desc:
                        cand_score = 20 + term_bonus
                    else:
                        cand_score = 0
                    if cand_score > score:
                        score = cand_score
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry is None:
                return None
            used_indices.add(best_entry[0])
            matched.append((best_entry[0], best_entry[1], label, value))

        matched.sort(key=lambda item: item[0])
        return [(sel, label, value) for _idx, sel, label, value in matched]

    def _select_selectpicker_option(self, select_el, label: str, value: str) -> str:
        chosen = self.driver.execute_script(
            "var sel = arguments[0], wanted = (arguments[1] || '').trim().toLowerCase();"
            "var opts = Array.from(sel.options || []).map(function(o) {"
            "  return {value: o.value, text: (o.textContent || '').trim()};"
            "}).filter(function(o) { return wanted === '' || o.value !== ''; });"
            "var match = opts.find(function(o) { return o.text.toLowerCase() === wanted; })"
            "  || opts.find(function(o) { return o.text.toLowerCase().indexOf('(' + wanted + ')') !== -1; })"
            "  || opts.find(function(o) { return o.text.toLowerCase().indexOf(wanted) !== -1; })"
            "  || opts.find(function(o) { return o.value.toLowerCase() === wanted; });"
            "return match || null;",
            select_el,
            value,
        )
        if not chosen:
            raise LookupError(f"Option '{value}' not found in '{label}' filter dropdown.")

        self.driver.execute_script(
            "var sel = arguments[0], val = arguments[1];"
            "if (window.jQuery && window.jQuery.fn && window.jQuery.fn.selectpicker) {"
            "  window.jQuery(sel).selectpicker('val', val);"
            "  window.jQuery(sel).trigger('change');"
            "} else {"
            "  sel.value = val;"
            "  sel.dispatchEvent(new Event('change', {bubbles: true}));"
            "  if (window.jQuery) window.jQuery(sel).trigger('change');"
            "}",
            select_el,
            chosen["value"],
        )
        time.sleep(0.3)
        self.wait_for_ajax_idle()
        return chosen["text"]

    def apply_label_filters(self, filters: dict[str, str], expected_text: str) -> None:
        if not filters:
            raise LookupError("No filter field values were provided for this test case.")
        if not expected_text:
            raise LookupError("Expected filter result text is empty.")

        selectpicker_matches = self._match_selectpicker_filters(filters)
        if selectpicker_matches is not None:
            all_selects = self.driver.find_elements(
                By.CSS_SELECTOR, self.SELECTPICKER_FILTER_SELECTOR
            )
            targets = []
            for select_el, label, value in selectpicker_matches:
                el_id = select_el.get_attribute("id") or ""
                dom_pos = all_selects.index(select_el) if select_el in all_selects else -1
                targets.append((select_el, el_id, dom_pos, label, value))

            self._open_filter_panel()
            for select_el, el_id, dom_pos, label, value in targets:
                target_el = select_el
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
            self.assert_table_contains(expected_text, "filtered result")
            return

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
        time.sleep(0.4)

        # If daterangepicker shows preset ranges (Today, Yesterday, Custom Range), click 'Custom Range'
        custom_ranges = [
            el
            for el in self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'daterangepicker')]//li[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'custom')]",
            )
            if el.is_displayed()
        ]
        if custom_ranges:
            self.click(custom_ranges[0])
            time.sleep(0.3)

        start_els = self.visible_elements(*self.DATERANGE_START_LOCATOR)
        end_els = self.visible_elements(*self.DATERANGE_END_LOCATOR)
        if start_els and end_els:
            start_el, end_el = start_els[0], end_els[0]
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
            return

        # Fallback: set the daterange input directly and click Apply / press Enter
        sample = picker_input.get_attribute("value") or ""
        sep = " - " if " - " in sample else (" to " if " to " in sample else " - ")
        first_part = sample.split(sep)[0].strip() if sep in sample else sample
        start_str = self._format_for_picker(date_from, first_part)
        end_str = self._format_for_picker(date_to, first_part)
        combined = f"{start_str}{sep}{end_str}"

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
        if expected_text.strip() == "*":
            if self.report_table(timeout=10) is None:
                raise AssertionError("Report table was not visible after applying date range.")
            return
        self.assert_table_contains(expected_text, "date-filtered result")
        
    def sort_columns(self, labels: list[str]) -> None:
        table = self.report_table()
        if table is None:
            raise AssertionError("Cannot sort because the report table is missing.")

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

        # Fallback: Robo2mation custom Bootstrap length dropdown (.length_change)
        toggles = self.visible_elements(
            By.CSS_SELECTOR,
            ".dataTables_length .length_change > a, .length-option .dropdown > a",
        )
        if toggles:
            wanted = size.strip().casefold()
            current_els = self.visible_elements(
                By.CSS_SELECTOR,
                ".dataTables_length #current-length, .length-option #current-length",
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
                    opt
                    for opt in options
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
                available = [
                    (opt.get_attribute("data-value") or opt.text).strip()
                    for opt in options
                ]
                raise LookupError(
                    f"Page-size option '{size}' not found. Available: {available}"
                )
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

        target = self._find_export_item(key)
        if target is not None:
            self.click(target)
            time.sleep(0.4)
            return target

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
                for close_btn in self.visible_elements(
                    By.CSS_SELECTOR,
                    "[data-notify] .close, .alert .close, button[data-dismiss='alert']",
                ):
                    try:
                        self.driver.execute_script("arguments[0].click();", close_btn)
                    except Exception:
                        pass
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