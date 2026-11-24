"""Page Object for My Documents (Explorer), Quick/Advanced Search, Saved Search & Restore."""
from __future__ import annotations

from datetime import datetime
import os
import re
import time
import zipfile

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class ExplorerPage(BasePage):
    """Encapsulates Document Explorer tree/grid/list, Search, Saved Search, and Restore."""

    # Quick & Advanced Search
    SEARCH_BOX = (By.ID, "search_text")
    SEARCH_RESULTS = (By.ID, "search_result_list_group")
    FILTER_BTN = (By.CSS_SELECTOR, "button.filter-btn")
    SEARCH_MODAL = "#search_modal"
    SEARCH_NEXT_PAGE = "#search_pagination li.next:not(.disabled) a"
    SKIP_CHECKBOX_IDS = ("include_archive", "match_all", "select_all_search_result")

    # Saved Search (#seved_search_modal — matches application DOM ID spelling)
    SAVED_SEARCH_LIMIT = 5
    SAVED_SEARCH_MODAL = "#seved_search_modal"

    # Explorer Tree & Views
    TREE_ID = "left_cat_doc_explorer"
    LIST_CSS = "#explorer_file_list_view"
    NEXT_PAGE_CSS = "#paginate_explorer li.page-item.next:not(.disabled) a"
    DOCUMENTS_CSS = "#main-window .file-thumb, #main-window table tbody tr, #file_manager_content table tbody tr"
    CHILDREN_XPATH = "./ul/li/a[contains(@class,'jstree-anchor')]"

    DATE_PATTERN = re.compile(
        r"\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?|"
        r"[A-Za-z]{3}\s+\d{1,2},\s+\d{4}(?:,\s+\d{1,2}:\d{2}\s*[APap][Mm])?|"
        r"\d{1,2}[-/ ][A-Za-z]{3}[-/ ,]+\d{4}|\d{1,2}/\d{1,2}/\d{4}"
    )
    DATE_FORMATS = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%b %d, %Y, %I:%M %p",
        "%b %d, %Y",
        "%d-%b-%Y %H:%M:%S",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d/%m/%Y",
        "%d-%b, %Y",
        "%d %b, %Y",
    )

    def open(self) -> None:
        self.driver.get(cfg.EXPLORER_URL)
        self.wait_for_page_load()

    
    # Quick Search & Opening Documents
    

    def quick_search_for(self, query: str, expected: str, tries: int = 5) -> tuple[bool, int]:
        """Search in the global quick-search box and return (found, result_count)."""
        count = 0
        for _ in range(tries):
            self.driver.get(cfg.EXPLORER_URL)
            box = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BOX))
            box.clear()
            box.send_keys(query)
            try:
                WebDriverWait(self.driver, 6, ignored_exceptions=(StaleElementReferenceException,)).until(
                    lambda d: expected in d.find_element(*self.SEARCH_RESULTS).text
                )
                results = self.driver.find_element(*self.SEARCH_RESULTS)
                return True, len(results.find_elements(By.TAG_NAME, "a"))
            except TimeoutException:
                results = self.driver.find_element(*self.SEARCH_RESULTS)
                count = len(results.find_elements(By.TAG_NAME, "a"))
                if expected in results.text:
                    return True, count
            time.sleep(1.5)
        return False, count

    def search_finds(self, name: str, tries: int = 1) -> bool:
        for _ in range(tries):
            self.driver.get(cfg.EXPLORER_URL)
            box = self.wait.until(EC.element_to_be_clickable(self.SEARCH_BOX))
            box.clear()
            box.send_keys(name)
            try:
                WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
                    lambda d: name in d.find_element(*self.SEARCH_RESULTS).text
                )
                return True
            except TimeoutException:
                pass
        return False

    def open_document(self, name: str) -> None:
        """Find `name` via quick search and open its Document View in a new tab."""
        if not self.search_finds(name, tries=5):
            raise SetupError(f"document '{name}' not found in quick search")
        old_tabs = list(self.driver.window_handles)

        def _find_and_click(d):
            rows = d.find_elements(
                By.XPATH, f"//*[@id='search_result_list_group']//a[contains(., {self.xpath_text(name)})]"
            )
            if not rows:
                return False
            row = rows[0]
            open_btns = row.find_elements(By.CSS_SELECTOR, ".openInNew")
            self.click(open_btns[0] if open_btns else row)
            return True

        WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
            _find_and_click
        )
        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > len(old_tabs))
        self.switch_to_new_tab(old_tabs)
        self.wait_for_page_load()


    # Advanced Search
    

    def _find_search_meta_field(self, label_text: str):
        field = self.find_field(label_text)
        if field is not None:
            return field
        wanted = self.clean(label_text)

        def _find(d):
            for line in d.find_elements(By.CSS_SELECTOR, "#dms_search_form .meta-data-wrap .fg-line"):
                if line.is_displayed():
                    txt = self.clean(line.text)
                    if txt == wanted or txt.startswith(wanted):
                        inputs = line.find_elements(By.CSS_SELECTOR, "input[id]:not([type='hidden'])")
                        if inputs:
                            return inputs[0]
            for el in d.find_elements(
                By.XPATH,
                "//form[@id='dms_search_form']//div[contains(@class, 'meta-data-wrap')]"
                "//*[(self::input or self::textarea) and not(ancestor::*[contains(@class, 'bs-searchbox')])]",
            ):
                if not el.is_displayed():
                    continue
                el_id = self.clean(el.get_attribute("id") or "")
                el_name = self.clean(el.get_attribute("name") or "")
                container_text = ""
                try:
                    container = el.find_element(
                        By.XPATH, "ancestor::div[contains(@class, 'form-group') or contains(@class, 'fg-line')][1]"
                    )
                    container_text = self.clean(container.text.split(":", 1)[0])
                except Exception:
                    pass
                if wanted in (el_id, el_name, container_text) or container_text.startswith(wanted):
                    return el
            return None

        return _find(self.driver)

    def fill_search_meta(self, label_text: str, value: str) -> None:
        try:
            WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda _d: self._find_search_meta_field(label_text)
            )
        except TimeoutException as exc:
            names = [
                self.clean(el.text)
                for el in self.driver.find_elements(By.CSS_SELECTOR, "#dms_search_form .meta-data-wrap .fg-line")
            ]
            raise SetupError(f"search form has no metadata field '{label_text}'. Fields on page: {names}") from exc

        for _ in range(5):
            try:
                field = self._find_search_meta_field(label_text)
                if field is not None and field.get_attribute("value") != value:
                    field.clear()
                    field.send_keys(value)
                time.sleep(0.4)
                refreshed = self._find_search_meta_field(label_text)
                if refreshed is not None and refreshed.get_attribute("value") == value:
                    return
            except StaleElementReferenceException:
                time.sleep(0.4)
        raise SetupError(f"metadata field '{label_text}' in the search form does not keep the value '{value}'")

    def wait_search_meta_rebuilt(self, old_children: list, seconds: int = 5) -> None:
        if not old_children:
            self.wait_for_ajax_idle(timeout=seconds)
            return
        try:
            WebDriverWait(self.driver, seconds).until(EC.staleness_of(old_children[0]))
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=seconds)

    def advanced_search(
        self,
        name: str | None,
        include_archive: bool = False,
        match_all: bool = True,
        doc_type: str | None = None,
        extra: list[tuple[str, str]] | None = None,
        submit: bool = True,
    ) -> None:
        if not self.visible("#dms_search_form"):
            self.click(self.wait.until(EC.element_to_be_clickable(self.FILTER_BTN)))
        box = self.wait.until(EC.visibility_of_element_located((By.ID, "docname")))
        box.clear()
        box.send_keys(name or "")
        if doc_type:
            old_meta = self.driver.find_elements(By.CSS_SELECTOR, "#dms_search_form .meta-data-wrap .fg-line")
            self.pick_select2_by_id("documentType", doc_type)
            self.wait_search_meta_rebuilt(old_meta)
        for field_label, value in (extra or []):
            self.fill_search_meta(field_label, value)
        for checkbox_id, wanted in (("include_archive", include_archive), ("match_all", match_all)):
            if self.driver.find_element(By.ID, checkbox_id).is_selected() != wanted:
                self.click(self.driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}'].ts-helper"))
        if submit:
            self.click(self.driver.find_element(By.ID, "search_btn"))

            def _results_loaded(d) -> bool:
                if not self.visible(self.SEARCH_MODAL) or self.visible("#search_modal .loader"):
                    return False
                if self._search_result_rows_text():
                    return True
                content = d.find_elements(By.ID, "search_history_content")
                return bool(content and "no search result found" in (content[0].text or "").lower())

            try:
                WebDriverWait(self.driver, 15).until(_results_loaded)
            except TimeoutException:
                pass
            self.wait_for_ajax_idle(timeout=5)

    def advanced_finds(self, name: str, **options) -> bool:
        self.driver.get(cfg.EXPLORER_URL)
        self.advanced_search(name, **options)
        return bool(self.find_in_search_result_pages([name], max_pages=10))

    def advanced_search_result_names(self, max_pages: int = 10) -> list[str]:
        """Collect ordered filenames from `#search_modal tbody tr` across pages."""
        names: list[str] = []
        seen_pages: set[str] = set()
        for page in range(1, max_pages + 1):
            rows_js = self.driver.execute_script(
                "return Array.from(document.querySelectorAll('#search_modal tbody tr')).map(r => {"
                "  var tds = r.querySelectorAll('td');"
                "  return tds.length >= 3 ? tds[2].innerText.trim() : r.innerText.trim();"
                "});"
            ) or []
            sig = "|".join(rows_js)
            if not rows_js or sig in seen_pages:
                break
            seen_pages.add(sig)
            names.extend(rows_js)
            if page >= max_pages:
                break
            next_links = self.driver.find_elements(By.CSS_SELECTOR, self.SEARCH_NEXT_PAGE)
            if not next_links or not next_links[0].is_displayed():
                break
            self.click(next_links[0])
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda _d: not self.visible("#search_modal .loader")
                    and "|".join(
                        self.driver.execute_script(
                            "return Array.from(document.querySelectorAll('#search_modal tbody tr')).map(r => {"
                            "  var tds = r.querySelectorAll('td');"
                            "  return tds.length >= 3 ? tds[2].innerText.trim() : r.innerText.trim();"
                            "});"
                        ) or []
                    ) != sig
                )
            except TimeoutException:
                break
        return names

    def open_from_advanced_search(self, name: str) -> None:
        old_tabs = list(self.driver.window_handles)
        row = self.driver.find_element(By.XPATH, f"//tr[contains(., {self.xpath_text(name)})]")
        action_els = [
            el for el in row.find_elements(
                By.XPATH,
                ".//*[contains(@class, 'openInNew') or contains(@title, 'Open') or contains(@data-original-title, 'Open')] | "
                ".//td[last()]//*[self::a or self::button or self::i]",
            )
            if el.is_displayed()
        ]
        if action_els:
            self.click(action_els[-1])
        else:
            self.double_click_label(name)

        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > len(old_tabs))
        self.switch_to_new_tab(old_tabs)
        self.wait_for_page_load()

    def _search_result_rows_text(self) -> str:
        return (
            self.driver.execute_script(
                "return Array.from(document.querySelectorAll('#search_modal tbody tr')).map(r => r.innerText).join('\\n');"
            )
            or ""
        ).lower()

    def find_in_search_result_pages(self, names: list[str], max_pages: int = 50) -> dict[str, int]:
        """Walk paged Advanced Search results and return {name: page_number}."""
        found: dict[str, int] = {}
        page = 1
        for _ in range(max_pages * 2):
            text = self._search_result_rows_text()
            for name in names:
                if name not in found and name.lower() in text:
                    found[name] = page
            if len(found) == len(names) or page >= max_pages:
                break
            try:
                next_links = self.driver.find_elements(By.CSS_SELECTOR, self.SEARCH_NEXT_PAGE)
                if not next_links or not next_links[0].is_displayed():
                    break
                self.click(next_links[0])
            except StaleElementReferenceException:
                time.sleep(0.4)
                continue
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda _d: not self.visible("#search_modal .loader")
                    and self._search_result_rows_text()
                    and self._search_result_rows_text() != text
                )
            except TimeoutException:
                break
            page += 1
        return found

    def _result_checkboxes(self) -> list:
        for scope in (self.MODAL, ""):
            boxes = [
                b for b in self.driver.find_elements(By.XPATH, f"{scope}//input[@type='checkbox']")
                if b.get_attribute("id") not in self.SKIP_CHECKBOX_IDS
                and "select_all" not in (b.get_attribute("class") or "")
            ]
            if boxes:
                return boxes
        return []

    def _tick_checkbox(self, box) -> None:
        if box.is_displayed():
            self.click(box)
            return
        box_id = box.get_attribute("id")
        labels = [lb for lb in self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{box_id}']") if lb.is_displayed()] if box_id else []
        if labels:
            self.click(labels[0])
        else:
            self.driver.execute_script("arguments[0].click();", box)

    def download_multiple_from_advanced_search(self, doc_type: str | None = None) -> tuple[bool, str]:
        target_doc_type = (doc_type or cfg.DOC_TYPE_SEARCH_TERMS[0]).strip()

        self.driver.get(cfg.REQUESTED_DOWNLOAD_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=5)
        existing_hrefs = {
            a.get_attribute("href")
            for a in self.driver.find_elements(By.CSS_SELECTOR, "#requested_downloads tbody a[href]")
        }

        self.driver.get(cfg.EXPLORER_URL)
        self.advanced_search("", doc_type=target_doc_type)

        if "no search result found" in self.body_text():
            return False, f"advanced search found no document for doc type '{target_doc_type}'"
        boxes = self._result_checkboxes()
        if len(boxes) < 2:
            return False, f"document check boxes not found in the search result (found {len(boxes)})"
        for box in boxes[:2]:
            self._tick_checkbox(box)

        ok_toast, toast_msg = self.message_after(lambda: self.click_label("download"))
        if not ok_toast or "requested download" not in toast_msg.lower():
            return False, f"unexpected response when requesting bulk download: '{toast_msg}'"

        self.wait_for_ajax_idle(timeout=5)
        self.driver.get(cfg.REQUESTED_DOWNLOAD_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=5)

        attempts = 0

        def _find_new_link(d):
            nonlocal attempts
            if attempts > 0:
                d.refresh()
                self.wait_for_page_load()
                self.wait_for_ajax_idle(timeout=5)
            attempts += 1
            links = self.visible("#requested_downloads tbody a[href]")
            for ln in links:
                if ln.get_attribute("href") not in existing_hrefs:
                    return ln
            return links[0] if links and not existing_hrefs else None

        try:
            dl_link = WebDriverWait(self.driver, 45, poll_frequency=4).until(_find_new_link)
        except TimeoutException:
            return False, "no new download link appeared on Requested Downloads page"

        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        started = time.time()
        self.click(dl_link)
        file_name = self.wait_for_download(before, started=started)
        if not file_name or not file_name.lower().endswith(".zip"):
            return False, f"zip file was not downloaded (got: {file_name})"

        zip_path = os.path.join(str(cfg.DOWNLOAD_DIR), file_name)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                bad = zf.testzip()
                entries = zf.namelist()
        except zipfile.BadZipFile as exc:
            return False, f"downloaded file '{file_name}' is not a valid zip archive: {exc}"
        if bad is not None or len(entries) < 2:
            return False, f"zip '{file_name}' invalid or incomplete (bad={bad}, entries={entries})"
        return True, f"Requested Download generated ({toast_msg}); zip '{file_name}' verified with {len(entries)} files"

    def search_meta_values(self) -> list[str]:
        inputs = self.driver.find_elements(
            By.CSS_SELECTOR, "#dms_search_form .meta-data-wrap input[id]:not([type='hidden'])"
        )
        return [i.get_attribute("value") or "" for i in inputs]

    @staticmethod
    def build_cross_search_criteria(first: dict, second: dict) -> tuple[str | None, list[tuple[str, str]]]:
        """Build search (name, extra_meta_pairs) combining criteria from two different documents."""
        if len(first["values"]) >= 2 and len(second["values"]) >= 2:
            pairs = [
                (first["values"][0][0], first["values"][0][1]),
                (second["values"][1][0], second["values"][1][1]),
            ]
            return None, pairs
        if first["values"] and second["values"]:
            return first["name"], [(second["values"][0][0], second["values"][0][1])]
        raise SetupError("the doc-type has no text meta-data to search with")

    # ------------------------------------------------------------------
    # Saved Search (DMS-TC125, TC126)
    # ------------------------------------------------------------------

    def open_saved_search_list(self) -> list:
        self.driver.get(cfg.EXPLORER_URL)
        if not self.visible("#dms_search_form"):
            self.click(self.wait.until(EC.element_to_be_clickable(self.FILTER_BTN)))
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "saved_search"))))
        WebDriverWait(self.driver, 15).until(
            lambda _d: self.visible(f"{self.SAVED_SEARCH_MODAL} .saved_tr")
            or self.visible(f"{self.SAVED_SEARCH_MODAL} .save_search_no_data")
        )
        return self.visible(f"{self.SAVED_SEARCH_MODAL} .saved_tr")

    def free_saved_search_slot(self, prefix: str = "AUTO_SEARCH_") -> None:
        rows = self.open_saved_search_list()
        count = len(rows)
        for _ in range(count):
            if count < self.SAVED_SEARCH_LIMIT:
                break
            auto_rows = [
                r for r in self.visible(f"{self.SAVED_SEARCH_MODAL} .saved_tr")
                if r.text.strip().startswith(prefix)
            ]
            if not auto_rows:
                raise SetupError(
                    f"{count} saved searches exist (limit {self.SAVED_SEARCH_LIMIT}) and none is an {prefix}* test search"
                )
            row_id = auto_rows[0].get_attribute("data-id")
            self.click(auto_rows[0].find_element(By.CSS_SELECTOR, ".delete_save_search"))
            if not self.confirm("yes"):
                raise SetupError("delete confirmation for an old saved search did not appear")
            WebDriverWait(self.driver, 15).until(
                lambda d: not d.find_elements(By.CSS_SELECTOR, f"{self.SAVED_SEARCH_MODAL} .saved_tr[data-id='{row_id}'] td")
            )
            count -= 1

    def save_search(self, search_name: str, info: dict) -> tuple[bool, str]:
        self.free_saved_search_slot()
        self.driver.get(cfg.EXPLORER_URL)
        if info["values"]:
            self.advanced_search(None, doc_type=info["doc_type"], extra=info["values"][:1], submit=False)
        else:
            self.advanced_search(info["name"], doc_type=info["doc_type"], submit=False)

        def _action():
            self.click(self.driver.find_element(By.ID, "save_search_name"))
            name_box = WebDriverWait(self.driver, 10).until(lambda _d: self.modal_text_input())
            name_box.send_keys(search_name)
            self.click_label("save")

        return self.message_after(_action)

    def is_saved_search_listed(self, search_name: str) -> bool:
        rows = self.open_saved_search_list()
        return any(search_name.lower() in (r.text or "").lower() for r in rows)

    def load_saved_search_and_verify(self, search_name: str, info: dict) -> tuple[bool, str]:
        self.open_saved_search_list()
        self.wait_for_ajax_idle(timeout=5)
        self.double_click_label(search_name)
        self.wait_for_ajax_idle(timeout=5)

        if info["values"]:
            expected = info["values"][0][1]
            try:
                WebDriverWait(self.driver, 10).until(lambda _d: expected in self.search_meta_values())
                filled_ok, filled_msg = True, f"metadata '{expected}' was filled"
            except TimeoutException:
                filled_ok, filled_msg = False, f"metadata '{expected}' was NOT filled (form has {self.search_meta_values()})"
        else:
            expected = info["name"]
            filled = self.wait.until(EC.visibility_of_element_located((By.ID, "docname"))).get_attribute("value")
            filled_ok, filled_msg = (filled == expected), f"document name field has '{filled}' (expected '{expected}')"

        self.click(self.driver.find_element(By.ID, "search_btn"))
        try:
            WebDriverWait(self.driver, 15).until(
                lambda _d: self.visible(self.SEARCH_MODAL) and not self.visible("#search_modal .loader")
            )
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=5)
        shown = bool(self.find_in_search_result_pages([info["name"]], max_pages=10))
        search_msg = "Search shows the document" if shown else "Search does NOT show the document"
        return filled_ok and shown, f"Saved search '{search_name}' listed, double click: {filled_msg}; {search_msg}"

    # ------------------------------------------------------------------
    # My Documents Tree, Grid/List Views & Sorting
    # ------------------------------------------------------------------

    @staticmethod
    def _anchor_name(anchor) -> str:
        return (anchor.get_attribute("textContent") or "").strip()

    def _child_anchors(self, scope) -> list:
        anchors = scope.find_elements(By.XPATH, self.CHILDREN_XPATH)
        return [a for a in anchors if not self._anchor_name(a).lower().startswith("loading")]

    @staticmethod
    def sort_name(name: str) -> str:
        return os.path.splitext(name)[0].lower()

    @classmethod
    def parse_date(cls, text: str) -> datetime | None:
        match = cls.DATE_PATTERN.search(text or "")
        target = match.group(0).strip() if match else (text or "").strip()
        for fmt in cls.DATE_FORMATS:
            try:
                return datetime.strptime(target, fmt)
            except ValueError:
                continue
        return None

    def _navigate_tree_node(self, path: str) -> bool:
        """Select `path` in Explorer jsTree; return True if documents loaded, False if empty."""
        parts = [p.strip() for p in path.strip().strip("/").split("/") if p.strip()]
        self.driver.get(cfg.EXPLORER_URL)
        tree = self.wait.until(EC.presence_of_element_located((By.ID, self.TREE_ID)))
        WebDriverWait(self.driver, 30).until(lambda _d: self._child_anchors(tree))

        scope = tree
        target = None
        for i, part in enumerate(parts):
            anchors = self._child_anchors(scope)
            match = [a for a in anchors if self._anchor_name(a).lower() == part.lower()]
            if not match:
                names = [self._anchor_name(a) for a in anchors][:15]
                raise SetupError(f"'{part}' not found in the tree. Items there: {names}")
            target = match[0]
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            if i < len(parts) - 1:
                node_id = target.find_element(By.XPATH, "..").get_attribute("id")
                self.driver.execute_script(f"$('#{self.TREE_ID}').jstree('open_node', arguments[0]);", node_id)

                def _opened(drv):
                    try:
                        node = drv.find_element(By.ID, node_id)
                        return node if self._child_anchors(node) else False
                    except StaleElementReferenceException:
                        return False

                try:
                    scope = WebDriverWait(self.driver, 20).until(_opened)
                except TimeoutException as exc:
                    raise SetupError(f"category '{part}' did not open, or it has nothing inside") from exc

        leaf_id = target.find_element(By.XPATH, "..").get_attribute("id")
        self.driver.execute_script(
            f"var t = $('#{self.TREE_ID}').jstree(true); t.deselect_all(); t.select_node(arguments[0]);",
            leaf_id,
        )
        WebDriverWait(self.driver, 20).until(
            lambda _d: bool(self.visible(self.DOCUMENTS_CSS))
            or bool(self.visible("#main-window .no_cat_doc_selected_div"))
        )
        self.wait_for_ajax_idle(timeout=6)
        return not bool(self.visible("#main-window .no_cat_doc_selected_div"))

    def _filter_explorer_by_name(self, doc_name: str) -> None:
        search_btns = self.visible("#search_doc_explorer")
        if search_btns and not self.visible("#docname_explorer"):
            self.click(search_btns[0])
            self.wait.until(EC.visibility_of_element_located((By.ID, "docname_explorer")))
        box = self.wait.until(EC.visibility_of_element_located((By.ID, "docname_explorer")))
        box.clear()
        box.send_keys(doc_name)
        self.driver.execute_script("$('#docname_explorer').trigger('change');")
        try:
            WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda d: any(doc_name.lower() in r.text.lower() for r in self.visible("#explorer_file_list_view tbody tr"))
                or bool(self.visible("#main-window .no_cat_doc_selected_div"))
            )
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=5)

    def _find_explorer_row(self, doc_type: str, name: str):
        has_docs = self._navigate_tree_node(doc_type)
        if not has_docs:
            return None
        list_btns = self.visible("#list_view")
        if list_btns and not self.visible(self.LIST_CSS):
            self.click(list_btns[0])
            self.wait.until(lambda _d: bool(self.visible(self.LIST_CSS)))
        low = name.lower()
        for _ in range(3):
            try:
                for tr in self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} tbody tr"):
                    if low in (tr.text or "").lower():
                        return tr
                break
            except StaleElementReferenceException:
                time.sleep(0.3)
        self._filter_explorer_by_name(name)
        for _ in range(3):
            try:
                for tr in self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} tbody tr"):
                    if low in (tr.text or "").lower():
                        return tr
                return None
            except StaleElementReferenceException:
                time.sleep(0.3)
        return None

    def explorer_has(self, doc_type: str, name: str) -> bool:
        """Select `doc_type` in Explorer jsTree and verify `name` is listed in #explorer_file_list_view."""
        return self._find_explorer_row(doc_type, name) is not None

    def explorer_doc_icons(self, doc_type: str, name: str) -> dict[str, bool]:
        """Inspect Locked/Shared status icons on `name` inside Explorer list view."""
        row = self._find_explorer_row(doc_type, name)
        if row is None:
            return {"found": False, "locked": False, "shared": False}
        locked = bool(row.find_elements(By.CSS_SELECTOR, "i.fa-lock-keyhole[title='Locked']"))
        shared = bool(row.find_elements(By.CSS_SELECTOR, "i[title='Shared']"))
        return {"found": True, "locked": locked, "shared": shared}

    def explorer_content_search(self, doc_type: str, query: str, expected_name: str) -> tuple[bool, list[str]]:
        """Open `doc_type` in Explorer, type `query` in `#content-search`, and verify matching documents."""
        self._navigate_tree_node(doc_type)
        search_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "search_doc_explorer")))
        self.click(search_btn)
        box = self.wait.until(EC.visibility_of_element_located((By.ID, "content-search")))
        box.clear()
        box.send_keys(query)
        self.driver.execute_script("$('#content-search').trigger('change');")
        time.sleep(0.5)
        self.wait_for_ajax_idle(timeout=10)

        try:
            WebDriverWait(
                self.driver,
                15,
                ignored_exceptions=(StaleElementReferenceException,),
            ).until(
                lambda _d: bool(self.visible("#main-window .no_cat_doc_selected_div"))
                or bool(self.visible("#explorer_file_list_view tbody tr, #main-window .file-thumb"))
            )
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=6)

        def _visible_rows():
            return self.driver.execute_script("""
                var empty = document.querySelector('#main-window .no_cat_doc_selected_div');
                if (empty && empty.offsetParent !== null) return null;
                var out = [];
                document.querySelectorAll('#explorer_file_list_view tbody tr, #main-window .file-thumb .c-info').forEach(function(el) {
                    if (el.offsetParent === null) return;
                    var txt = (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
                    if (txt) out.push(txt);
                });
                return out;
            """)

        all_rows: list[str] = []
        for page in range(1, 21):
            rows = _visible_rows()
            if rows is None:
                return False, []
            all_rows.extend(rows)
            if any(expected_name.lower() in r.lower() for r in rows):
                return True, all_rows
            if page >= 20:
                break
            next_btns = [b for b in self.driver.find_elements(By.CSS_SELECTOR, self.NEXT_PAGE_CSS) if b.is_displayed()]
            if not next_btns:
                break
            prev_sig = "|".join(rows)
            self.click(next_btns[0])
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda _d: "|".join(_visible_rows() or []) != prev_sig
                )
            except TimeoutException:
                break
            self.wait_for_ajax_idle(timeout=4)
        return False, all_rows

    def open_doc_type_tree(self, path: str) -> None:
        if not self._navigate_tree_node(path):
            raise SetupError(f"'{path}' shows no documents, use a doc-type that has documents")

    def choose_order(self, label: str) -> None:
        self.pick_bootstrap_select("order_by", label)
        self.wait_for_ajax_idle(timeout=6)
        shown = self.driver.find_element(By.CSS_SELECTOR, "button[data-id='order_by'] .filter-option").text.strip()
        if shown.lower() != label.lower():
            raise SetupError(f"could not choose '{label}' in Order By (it shows '{shown}')")

    def page_rows(self) -> list[list[str]]:
        rows = []
        for tr in self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} tbody tr"):
            cells = [td.text.strip() for td in tr.find_elements(By.TAG_NAME, "td")]
            if len(cells) >= 4:
                rows.append(cells)
        return rows

    def read_pages(self, path: str, pages: int = 3) -> tuple[list[list[str]], int]:
        rows: list[list[str]] = []
        read = 0
        for _ in range(pages):
            rows += self.page_rows()
            read += 1
            buttons = self.driver.find_elements(By.CSS_SELECTOR, self.NEXT_PAGE_CSS)
            if not buttons or read == pages:
                break
            before = self.driver.find_element(By.CSS_SELECTOR, f"{self.LIST_CSS} tbody").text
            self.click(buttons[0])
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, f"{self.LIST_CSS} tbody").text != before
                )
            except TimeoutException:
                break
            self.wait_for_ajax_idle(timeout=4)
        if read < 2:
            raise SetupError(f"'{path}' has only one page of documents, use one with more than one page")
        return rows, read

    def verify_document_sorting(
        self,
        path: str,
        order_label: str | None = None,
        by: str = "name",
        descending: bool = False,
        label_desc: str = "",
    ) -> tuple[bool, str]:
        """Open `path` in Explorer, optionally choose Order By, and assert sorting across pages."""
        self.open_doc_type_tree(path)
        if order_label:
            self.choose_order(order_label)
        self.wait.until(lambda _d: self.visible(self.LIST_CSS))
        rows, pages = self.read_pages(path)
        if len(rows) < 2:
            return False, f"expected at least 2 document rows across {pages} pages, found {len(rows)}"
        desc = label_desc or f"{by.title()} {'descending' if descending else 'ascending'}"

        if by == "name":
            names = [row[1] for row in rows]
            for i in range(len(names) - 1):
                a, b = self.sort_name(names[i]), self.sort_name(names[i + 1])
                if (a < b) if descending else (a > b):
                    return False, (
                        f"NOT {desc}: '{names[i]}' is shown before '{names[i + 1]}'. "
                        f"{len(names)} documents checked over {pages} pages"
                    )
            return True, f"{len(names)} documents checked over {pages} pages: {desc}"

        dates = [self.parse_date(row[3]) for row in rows]
        if None in dates:
            bad = [row[3] for row, dt in zip(rows, dates) if dt is None][:3]
            return False, f"could not read the Uploaded At dates (examples: {bad})"
        for i in range(len(dates) - 1):
            if (dates[i] < dates[i + 1]) if descending else (dates[i] > dates[i + 1]):
                return False, (
                    f"NOT {desc}: '{rows[i][1]}' ({rows[i][3]}) is shown before "
                    f"'{rows[i + 1][1]}' ({rows[i + 1][3]}). {len(rows)} documents checked over {pages} pages"
                )
        return True, f"{len(rows)} documents checked over {pages} pages: {desc}"

    def verify_tree_default_sorting(self) -> tuple[bool, str]:
        self.driver.get(cfg.EXPLORER_URL)
        tree = self.wait.until(EC.presence_of_element_located((By.ID, self.TREE_ID)))
        WebDriverWait(self.driver, 30).until(lambda _d: self._child_anchors(tree))
        self.wait_for_ajax_idle(timeout=5)

        def _sort_key(name: str) -> str:
            return re.sub(r"[^a-z0-9]", "", name.lower())

        names = [self._anchor_name(a) for a in self._child_anchors(tree)]
        if len(names) < 2:
            return False, f"only {len(names)} category / doc-type names found on the page"
        for i in range(len(names) - 1):
            if _sort_key(names[i]) > _sort_key(names[i + 1]):
                return False, f"NOT sorted by name ascending: '{names[i]}' is shown before '{names[i + 1]}'. {len(names)} names checked"

        # Also verify child sorting inside a folder node when available
        child_checked = 0
        for anchor in self._child_anchors(tree):
            node = anchor.find_element(By.XPATH, "..")
            if "jstree-leaf" in (node.get_attribute("class") or ""):
                continue
            node_id = node.get_attribute("id")
            self.driver.execute_script(f"$('#{self.TREE_ID}').jstree('open_node', arguments[0]);", node_id)
            try:
                opened_node = WebDriverWait(self.driver, 8).until(
                    lambda d, nid=node_id: n if self._child_anchors(n := d.find_element(By.ID, nid)) else False
                )
                child_names = [self._anchor_name(c) for c in self._child_anchors(opened_node)]
                if len(child_names) >= 2:
                    child_checked = len(child_names)
                    for i in range(len(child_names) - 1):
                        if _sort_key(child_names[i]) > _sort_key(child_names[i + 1]):
                            return False, (
                                f"Child nodes under '{self._anchor_name(anchor)}' NOT sorted ascending: "
                                f"'{child_names[i]}' before '{child_names[i + 1]}'"
                            )
                    break
            except TimeoutException:
                continue

        return True, (
            f"{len(names)} root categories/doc-types and {child_checked} child items checked: sorted by name ascending"
        )

    def _verify_view_tab_and_quick_view(self, avatar_el, preview_el) -> tuple[bool, bool, str]:
        main_tab = self.driver.current_window_handle
        old_tabs = list(self.driver.window_handles)
        self.click(avatar_el)
        opened_ok = False
        tab_url = ""
        try:
            WebDriverWait(self.driver, 8).until(lambda d: len(d.window_handles) > len(old_tabs))
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.wait_for_page_load()
            tab_url = (self.driver.current_url or "").lower()
            opened_ok = "/dms/document/view/" in tab_url and "/login" not in tab_url
        except TimeoutException:
            opened_ok = False
        self.close_extra_tabs(main_tab)

        self.click(preview_el)
        self.wait_for_ajax_idle(timeout=6)
        try:
            quick_ok = WebDriverWait(self.driver, 10).until(
                lambda d: any(
                    m.is_displayed()
                    and bool(
                        m.find_elements(
                            By.CSS_SELECTOR,
                            "#file_container iframe[src], #file_container img[src], "
                            "#file_container audio[src], #file_container video[src], "
                            "#file_container object[data], .explorer-doc-preview table, #file_container p",
                        )
                    )
                    for m in d.find_elements(By.CSS_SELECTOR, "#viewFiles, #explorer_excel_ViewModal")
                )
            )
        except TimeoutException:
            quick_ok = False
        return opened_ok, bool(quick_ok), tab_url

    def test_grid_view(self, doc_type: str) -> tuple[bool, str]:
        self.open_doc_type_tree(doc_type)
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "grid_view"))))
        self.wait_for_ajax_idle(timeout=5)
        cards = self.visible("div.file-thumb a.ci-avatar")
        if not cards or self.visible(self.LIST_CSS):
            return False, "documents are not shown in grid view after clicking the grid icon"

        preview = self.visible("div.file-thumb a.quick_view")
        if not preview:
            return False, "Grid view shown, but the view (preview) icon was not found"
        opened_tab, quick_view, tab_url = self._verify_view_tab_and_quick_view(cards[0], preview[0])
        ok = opened_tab and quick_view
        return ok, (
            f"Grid view shown. Document opened in new tab ({tab_url}): {'yes' if opened_tab else 'NO'}. "
            f"Quick view modal opened with preview content: {'yes' if quick_view else 'NO'}"
        )

    def test_list_view(self, doc_type: str) -> tuple[bool, str]:
        self.open_doc_type_tree(doc_type)
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "grid_view"))))
        self.wait_for_ajax_idle(timeout=5)
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "list_view"))))
        self.wait_for_ajax_idle(timeout=5)
        if not self.visible(self.LIST_CSS) or self.visible("div.file-thumb"):
            return False, "documents are not shown in list view after clicking the list icon"

        headers = [th.text.strip().lower() for th in self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} thead th")]
        missing = [col for col in ("document name", "uploaded by") if col not in headers]
        if missing:
            return False, f"list view does not show the columns {missing} (found: {headers})"
        rows = self.page_rows()
        if not rows or not rows[0][1].strip() or not rows[0][2].strip():
            return False, f"list view first row is missing title/publisher cells ({rows[:1]})"

        avatars = self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} a.ci-avatar")
        preview = self.driver.find_elements(By.CSS_SELECTOR, f"{self.LIST_CSS} a.quick_view")
        if not avatars or not preview:
            return False, "List view shown, but document open or preview icon was not found"
        opened_tab, quick_view, tab_url = self._verify_view_tab_and_quick_view(avatars[0], preview[0])

        ok = opened_tab and quick_view
        return ok, (
            f"List view shows Document Name ('{rows[0][1]}') and Uploaded By ('{rows[0][2]}'). "
            f"Document opened in new tab ({tab_url}): {'yes' if opened_tab else 'NO'}. "
            f"Quick view modal opened with preview content: {'yes' if quick_view else 'NO'}"
        )

    def load_explorer_tree_names(self) -> list[str]:
        self.driver.get(cfg.EXPLORER_URL)
        tree = self.wait.until(EC.presence_of_element_located((By.ID, self.TREE_ID)))
        WebDriverWait(self.driver, 30).until(lambda _d: self._child_anchors(tree))
        self.wait_for_ajax_idle(timeout=6)
        return [self._anchor_name(a) for a in tree.find_elements(By.CSS_SELECTOR, "a.jstree-anchor")]

    def load_explorer_text(self) -> str:
        return "\n".join(self.load_explorer_tree_names()).lower()

    # ------------------------------------------------------------------
    # Restore Deleted Document (DMS-TC028)
    # ------------------------------------------------------------------

    def open_restore_page(self, name: str) -> bool:
        self.wait_for_ajax_idle(timeout=6)
        for _ in range(3):
            self.driver.get(cfg.RESTORE_URL)
            self.wait_for_ajax_idle(timeout=6)
            if "restore" not in self.driver.current_url.lower() or "no category/document type selected" in self.body_text():
                try:
                    self.click_label("Restore Documents")
                    self.wait_for_ajax_idle(timeout=5)
                except Exception:
                    pass
            if self.wait_text(name, 6):
                return True
        return False

    def restore_deleted_document(self, name: str) -> tuple[bool, str]:
        row = self.driver.find_element(
            By.XPATH, f"//table[@id='restore_data']//tbody//tr[contains(., {self.xpath_text(name)})]"
        )
        if "selected" not in (row.get_attribute("class") or ""):
            self.click(row.find_elements(By.TAG_NAME, "td")[0])
            self.wait_for_ajax_idle(timeout=4)

        restore_btn = next((b for b in self.driver.find_elements(By.ID, "restore_doc") if b.is_displayed()), None)
        if not restore_btn:
            restore_btn = self.find_by_label("restore")
        if not restore_btn:
            raise SetupError("Could not find the Restore button (#restore_doc) on the page")

        def _action():
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restore_btn)
            self.driver.execute_script("arguments[0].click();", restore_btn)

        ok, message = self.message_after(_action)
        self.wait_for_ajax_idle(timeout=6)
        return ok, message
