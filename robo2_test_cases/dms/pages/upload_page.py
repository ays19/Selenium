"""Page Object for Attach Documents, Pending Documents, Metadata Upload & Watermarks."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import os
import random
import re
import shutil
import time
import uuid

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class UploadPage(BasePage):
    """Encapsulates Standard Upload, Pending Documents list/grid, Metadata & Watermarks."""

    # Attach & Pending locators
    NEXT_BTN = (By.ID, "submit-all")
    DROPZONE_INPUT = (By.CSS_SELECTOR, "input.dz-hidden-input")
    DROPZONE_PREVIEW = (By.CSS_SELECTOR, ".dz-preview")
    DROPZONE_STATUS = (By.CSS_SELECTOR, ".dz-preview.dz-success, .dz-preview.dz-error")
    DROPZONE_ERRORS = (By.CSS_SELECTOR, ".dz-preview.dz-error .dz-error-message")
    DROPZONE_FILENAME = (By.CSS_SELECTOR, ".dz-preview .dz-filename")

    LIST_CONTAINER = (By.ID, "list_view_container")
    GRID_CONTAINER = (By.ID, "grid_view_container")
    LIST_VIEW_BTN = (By.ID, "list_view_btn")
    GRID_VIEW_BTN = (By.ID, "grid_view_btn")
    PENDING_ROW = (By.CSS_SELECTOR, "#list_view_container tr.pending-meta")
    PENDING_ITEM = (By.CSS_SELECTOR, ".pending-meta")
    SELECTED_DESELECT_ROWS = "#selected_file_div .deselect-row"
    SELECTED_DELETE_XPATH = (
        "//*[@id='selected_file_div']//*[contains(@class, 'deselect-row')]//i[contains(@class, 'delete-item')]"
    )
    VIEW_MODAL = (By.ID, "viewFiles")

    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self._created_watermarks: list[str] = []

    # Metadata form locators
    DOC_TYPE_BOX = (By.CSS_SELECTOR, "span.select2-selection[aria-labelledby='select2-DocumentType-container']")
    DOC_TYPE_RESULTS = "#select2-DocumentType-results"
    DOC_TYPE_OPTION = "#select2-DocumentType-results li.select2-results__option"
    DOC_TYPE_SEARCH_BOX = (
        By.XPATH,
        "//ul[@id='select2-DocumentType-results']/ancestor::span[contains(@class, 'select2-dropdown')]"
        "//input[contains(@class, 'select2-search__field')]",
    )
    DOC_TYPE_CONTAINER_TEXT = (By.ID, "select2-DocumentType-container")
    METADATA_PANEL = (By.ID, "add_meta_data")
    UPLOAD_BTN = (By.ID, "submit_meta_data")
    FILE_NAME_INPUT = (By.ID, "file_name")
    CHECKER_DIV = (By.ID, "checker-div")

    # Watermark modal locators
    WATERMARK_MODAL = (By.ID, "add_watermark_modal")
    WATERMARK_BTN = (By.ID, "add_watermark_button")
    WATERMARK_CUSTOM_TAB = "watermark_custom_text_tab"
    WATERMARK_UPLOAD_TAB = "watermark_upload_file_tab"
    WATERMARK_LIBRARY_TAB = "watermark_commonly_used_files_tab"
    WATERMARK_LIBRARY_CONTAINER = (By.ID, "watermark_commonly_used_files_container")

    # ------------------------------------------------------------------
    # Sample File Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def find_sample_file(ext: str) -> tuple[str, str] | None:
        sample_dir = str(cfg.SAMPLE_DIR)
        if not os.path.isdir(sample_dir):
            return None
        for name in os.listdir(sample_dir):
            if name.lower().endswith("." + ext.lower()):
                return name, os.path.abspath(os.path.join(sample_dir, name))
        return None

    @staticmethod
    def pick_sample_files(extensions: list[str], count: int) -> list[str]:
        sample_dir = str(cfg.SAMPLE_DIR)
        if not os.path.isdir(sample_dir):
            return []
        names = os.listdir(sample_dir)
        for ext in extensions:
            same = [n for n in names if n.lower().endswith("." + ext)]
            if len(same) >= count:
                return [os.path.abspath(os.path.join(sample_dir, n)) for n in same[:count]]
        mixed = [n for n in names if n.lower().endswith(tuple("." + e for e in extensions))]
        return [os.path.abspath(os.path.join(sample_dir, n)) for n in mixed[:count]] if len(mixed) >= count else []

    @staticmethod
    def unique_copy(path: str) -> tuple[str, str]:
        """Copy `path` with a unique filename and trailing bytes so checksum checks pass."""
        folder = os.path.join(str(cfg.DOWNLOAD_DIR), "upload_copies")
        os.makedirs(folder, exist_ok=True)
        name = datetime.now().strftime("AUTO%H%M%S%f")[:12] + "_" + os.path.basename(path)
        new_path = os.path.join(folder, name)
        shutil.copy2(path, new_path)
        with open(new_path, "ab") as f:
            f.write(("\n%unique " + uuid.uuid4().hex + "\n").encode())
        return name, new_path

    # ------------------------------------------------------------------
    # Attach Documents & Pending List / Grid View
    # ------------------------------------------------------------------

    def _next_is_ready(self) -> bool:
        try:
            btn = self.driver.find_element(*self.NEXT_BTN)
            return btn.is_enabled() and "disabled" not in (btn.get_attribute("class") or "").lower()
        except Exception:
            return False

    def attach_file_check(self, ext: str) -> tuple[bool, str]:
        """Attach a sample file on Standard Upload page and verify Dropzone accepts it."""
        sample = self.find_sample_file(ext)
        if not sample:
            return False, "sample file missing"
        file_name, path = sample
        max_bytes = 20 * 1024 * 1024
        if os.path.getsize(path) > max_bytes:
            return False, f"sample '{file_name}' exceeds 20 MB"

        self.driver.get(cfg.ATTACH_URL)
        try:
            file_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(self.DROPZONE_INPUT)
            )
        except TimeoutException:
            inputs = self.driver.find_elements(*self.FILE_INPUT)
            if not inputs:
                return False, "Dropzone file input not found"
            file_input = inputs[0]

        self.driver.execute_script(
            "arguments[0].style.display='block'; arguments[0].style.visibility='visible';",
            file_input,
        )
        file_input.send_keys(path)

        try:
            WebDriverWait(self.driver, 30).until(lambda d: d.find_elements(*self.DROPZONE_STATUS))
        except TimeoutException:
            return False, f"'{file_name}' did not finish Dropzone processing"

        errors = [
            e.text.strip()
            for e in self.driver.find_elements(*self.DROPZONE_ERRORS)
            if e.text.strip()
        ]
        if errors:
            return False, errors[0]

        shown_names = [
            (e.text or e.get_attribute("textContent") or "").strip().lower()
            for e in self.driver.find_elements(*self.DROPZONE_FILENAME)
        ]
        if file_name.lower() not in " ".join(shown_names):
            return False, f"'{file_name}' missing from Dropzone preview ({shown_names})"
        if not self._next_is_ready():
            return False, f"Next button (#submit-all) stayed disabled after attaching '{file_name}'"
        return True, f"attached '{file_name}'"

    def open_pending_list(self) -> None:
        self.driver.get(cfg.PENDING_URL)
        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER))
        if not self.visible("#list_view_container"):
            btns = self.driver.find_elements(*self.LIST_VIEW_BTN)
            if btns:
                self.click(btns[0])
                self.wait.until(lambda _d: bool(self.visible("#list_view_container")))
        try:
            WebDriverWait(self.driver, 12).until(
                lambda d: bool(d.find_elements(*self.PENDING_ROW))
                or bool(d.find_elements(By.CSS_SELECTOR, ".nothingPending"))
            )
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=8)

    def pending_page_info(self) -> tuple[str, int | None]:
        try:
            shown = self.driver.find_element(By.CSS_SELECTOR, ".showing-files").text.strip()
            total = self.driver.find_element(By.CSS_SELECTOR, ".total-files").text.strip()
        except Exception:
            return "", None
        return shown, int(total) if total.isdigit() else None

    def pending_next_page(self) -> bool:
        for _ in range(10):
            shown, total = self.pending_page_info()
            last = shown.split("-")[-1].strip()
            if total is not None and last.isdigit() and int(last) >= total:
                return False
            before_rows = tuple(
                r.get_attribute("data-pending-doc-name")
                for r in self.driver.find_elements(*self.PENDING_ROW)
            )
            more = [b for b in self.visible("#pagination button.next") if b.is_enabled()]
            if more:
                self.click(more[0])
                try:
                    WebDriverWait(self.driver, 15, ignored_exceptions=(StaleElementReferenceException,)).until(
                        lambda d: (
                            self.pending_page_info()[0] != shown
                            and bool(d.find_elements(*self.PENDING_ROW))
                            and tuple(
                                r.get_attribute("data-pending-doc-name")
                                for r in d.find_elements(*self.PENDING_ROW)
                            ) != before_rows
                        )
                    )
                except TimeoutException:
                    pass
                self.wait_for_ajax_idle(timeout=5)
                return True
            if not shown:
                return False
            time.sleep(0.5)
        return False

    def pending_names(self) -> list[str]:
        names, seen = [], set()
        for _ in range(30):
            page = [
                r.get_attribute("data-pending-doc-name")
                for r in self.driver.find_elements(*self.PENDING_ROW)
            ]
            if tuple(page) in seen:
                break
            seen.add(tuple(page))
            names += page
            if not self.pending_next_page():
                break
        return names

    def selected_count(self) -> int:
        return len(self.visible(self.SELECTED_DESELECT_ROWS))

    def clear_selected_files(self) -> None:
        for _ in range(20):
            icons = self.driver.find_elements(By.XPATH, self.SELECTED_DELETE_XPATH)
            if not icons:
                return
            before_count = len(icons)
            self.driver.execute_script("arguments[0].click();", icons[0])
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: len(d.find_elements(By.XPATH, self.SELECTED_DELETE_XPATH)) < before_count
                )
            except TimeoutException:
                pass

    @classmethod
    def _pending_row_icon(cls, file_name: str):
        return (
            By.XPATH,
            f"//*[@id='list_view_container']//tr[@data-pending-doc-name={cls.xpath_text(file_name)}]"
            f"//i[contains(@class, 'add-item')]",
        )

    def click_pending_icon(self, file_name: str) -> bool:
        for attempt in range(2):
            for _ in range(30):
                self.wait_for_ajax_idle(timeout=4)
                icons = [i for i in self.driver.find_elements(*self._pending_row_icon(file_name)) if i.is_displayed()]
                if icons:
                    self.click(icons[0])
                    return True
                if not self.pending_next_page():
                    break
            if attempt == 0:
                self.open_pending_list()
        return False

    def attach_new_file(self, path: str) -> str | None:
        """Attach `path` via Dropzone on Attach Documents and return its Pending Files name."""
        self.open_pending_list()
        before = Counter(self.pending_names())
        self.driver.get(cfg.ATTACH_URL)
        try:
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(self.DROPZONE_INPUT)
            )
        except TimeoutException as exc:
            raise SetupError(
                f"the Dropzone file input was not found on the Attach Documents page: {self.driver.current_url}"
            ) from exc

        file_input.send_keys(path)
        try:
            WebDriverWait(self.driver, 60).until(lambda d: d.find_elements(*self.DROPZONE_STATUS))
        except TimeoutException:
            pass

        errors = [
            e.text.strip()
            for e in self.driver.find_elements(*self.DROPZONE_ERRORS)
            if e.text.strip()
        ]
        if errors:
            print(f"   Attach Documents page refused the file: {errors[0]}")
            return None

        for _ in range(6):
            time.sleep(2)
            self.open_pending_list()
            new = Counter(self.pending_names()) - before
            if new:
                return next(iter(new))
        return None

    def attach_and_get_pending_names(self, paths: list[str]) -> list[str]:
        pending_names = []
        for path in paths:
            _, copy_path = self.unique_copy(path)
            name = self.attach_new_file(copy_path) or self.attach_new_file(path)
            if not name:
                raise SetupError(f"could not attach '{os.path.basename(path)}' to Pending Files")
            pending_names.append(name)
        return pending_names

    def find_pending_row(self, file_name: str):
        for _ in range(30):
            rows = [
                r for r in self.driver.find_elements(
                    By.XPATH,
                    f"//tr[contains(@class,'pending-meta') and @data-pending-doc-name={self.xpath_text(file_name)}]",
                )
                if r.is_displayed()
            ]
            if rows:
                return rows[0]
            if not self.pending_next_page():
                return None
        return None

    def has_ocr_icon(self, file_name: str) -> bool:
        self.open_pending_list()
        row = self.find_pending_row(file_name)
        if row is None:
            raise SetupError(f"pending file '{file_name}' was not found in Pending Documents list")
        return any(el.is_displayed() for el in row.find_elements(By.CSS_SELECTOR, ".ocr-item"))

    def run_pending_ocr(self, file_name: str, timeout: int = 60) -> tuple[bool, str]:
        self.open_pending_list()
        row = self.find_pending_row(file_name)
        if row is None:
            return False, f"pending file '{file_name}' not found"
        icons = [el for el in row.find_elements(By.CSS_SELECTOR, ".ocr-item") if el.is_displayed()]
        if not icons:
            return False, f"OCR icon (.ocr-item) not shown for '{file_name}'"
        ok, msg = self.message_after(lambda: self.click(icons[0]), seconds=timeout)
        try:
            WebDriverWait(self.driver, timeout).until(lambda _d: not self.visible(".blockUI"))
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=5)
        return ok, msg

    def select_pending_files(self, pending_names: list[str]) -> None:
        self.open_pending_list()
        self.clear_selected_files()
        for idx, name in enumerate(pending_names):
            if idx > 0:
                self.open_pending_list()
            if not self.click_pending_icon(name):
                raise SetupError(f"pending file '{name}' could not be selected")
            WebDriverWait(self.driver, 8).until(lambda _d, n=idx + 1: self.selected_count() >= n)

    def _find_grid_view_icon(self, ext: str):
        icon = self.driver.execute_script(
            """
            function vis(el) {
                return !!(el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
            }
            var suffix = '.' + String(arguments[0] || '').toLowerCase();
            var cards = document.querySelectorAll('#grid_view_container .pending-meta');
            if (!cards.length) cards = document.querySelectorAll('.pending-meta');
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i];
                if (!vis(card)) continue;
                var name = (card.getAttribute('data-pending-doc-name') || '').trim().toLowerCase();
                if (!name.endsWith(suffix)) continue;
                var icons = card.querySelectorAll('.view-item');
                for (var j = 0; j < icons.length; j++) {
                    if (vis(icons[j])) return icons[j];
                }
            }
            return null;
            """,
            ext,
        )
        if icon is not None:
            return icon
        raise LookupError(f"no visible .{ext} card with view icon")

    def _locate_view_icon_across_pages(self, ext: str):
        for _ in range(15):
            try:
                return self._find_grid_view_icon(ext)
            except Exception:
                if not self.pending_next_page():
                    break
                if not self.visible("#grid_view_container"):
                    btns = self.driver.find_elements(*self.GRID_VIEW_BTN)
                    if btns:
                        self.click(btns[0])
                        WebDriverWait(self.driver, 5, poll_frequency=0.1).until(
                            lambda _d: bool(self.visible("#grid_view_container"))
                        )
        return None

    def _preview_result(self, old_tabs: list[str], ext: str) -> str | None:
        if len(self.driver.window_handles) > len(old_tabs):
            self.driver.switch_to.window(self.driver.window_handles[-1])
            url = (self.driver.current_url or "").lower()
            self.driver.switch_to.window(old_tabs[0])
            if url and not url.startswith("about:blank") and "/login" not in url:
                return "preview opened in new tab"
            return None

        return self.driver.execute_script(
            """
            function vis(el) {
                return !!(el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
            }
            if (window.jQuery && window.jQuery.active > 0) return null;
            var vf = document.getElementById('viewFiles');
            if (!vis(vf)) return null;
            var loaders = vf.querySelectorAll('.loading-spinner, .loader, #loading');
            for (var k = 0; k < loaders.length; k++) {
                if (vis(loaders[k])) return null;
            }
            var media = vf.querySelectorAll(
                '#file_container iframe[src], #file_container img[src], ' +
                '#file_container audio[src], #file_container video[src], ' +
                '#file_container object[data], .temp-modal-preview table.preview-table'
            );
            for (var i = 0; i < media.length; i++) {
                if (vis(media[i])) return 'preview opened';
            }
            var fc = document.getElementById('file_container');
            var txt = (fc ? (fc.innerText || fc.textContent || '') : '').toLowerCase();
            if (txt.indexOf('preview') !== -1 && (
                txt.indexOf('not available') !== -1 ||
                txt.indexOf('unavailable') !== -1 ||
                txt.indexOf('not supported') !== -1
            )) {
                return "'Preview Not Available!' message shown";
            }
            return null;
            """
        )

    def _is_pending_grid_open(self) -> bool:
        cur = (self.driver.current_url or "").split("?")[0].split("#")[0].rstrip("/")
        want = cfg.PENDING_URL.rstrip("/")
        return cur == want and bool(self.visible("#grid_view_container"))

    def _open_pending_grid_view(self) -> bool:
        self.driver.get(cfg.PENDING_URL)
        self.wait.until(EC.presence_of_element_located(self.LIST_CONTAINER))
        try:
            self.wait.until(EC.element_to_be_clickable(self.GRID_VIEW_BTN)).click()
            WebDriverWait(self.driver, 10, poll_frequency=0.1).until(
                lambda _d: bool(self.visible("#grid_view_container"))
            )
            WebDriverWait(self.driver, 10, poll_frequency=0.1).until(
                lambda d: bool(
                    d.execute_script(
                        "function vis(el) { return !!(el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden'); }"
                        "var els = document.querySelectorAll('#grid_view_container .pending-meta');"
                        "for (var i = 0; i < els.length; i++) { if (vis(els[i])) return true; }"
                        "return !!document.querySelector('.nothingPending');"
                    )
                )
            )
            self.wait_for_ajax_idle(timeout=5)
            return True
        except Exception:
            return False

    def view_pending_document(self, ext: str) -> tuple[bool, str]:
        """Switch Pending Documents to Grid View, preview a `.ext` file, and close the preview."""
        reused_grid = self._is_pending_grid_open()
        if not reused_grid and not self._open_pending_grid_view():
            return False, "Grid View icon not found"

        icon = None
        if reused_grid:
            try:
                icon = self._find_grid_view_icon(ext)
            except LookupError:
                shown, _ = self.pending_page_info()
                if shown and not re.match(r"^1\s*-", shown):
                    if not self._open_pending_grid_view():
                        return False, "Grid View icon not found"
                icon = self._locate_view_icon_across_pages(ext)
        else:
            icon = self._locate_view_icon_across_pages(ext)

        if icon is None:
            sample = self.find_sample_file(ext)
            if sample:
                _, copy_path = self.unique_copy(sample[1])
                self.attach_new_file(copy_path)
                if not self._open_pending_grid_view():
                    return False, "Grid View failed after attaching sample"
                icon = self._locate_view_icon_across_pages(ext)
        if icon is None:
            return False, f"no .{ext} document in pending list"

        old_tabs = list(self.driver.window_handles)
        try:
            self.click(icon)
            result = WebDriverWait(self.driver, 12, poll_frequency=0.1).until(
                lambda _d: self._preview_result(old_tabs, ext)
            )
        except Exception:
            return False, f"no preview content loaded after clicking view icon for .{ext}"

        if len(self.driver.window_handles) > len(old_tabs):
            self.close_extra_tabs(old_tabs[0])
        else:
            self._close_preview_modal()
        return True, result

    def _close_preview_modal(self) -> None:
        def _closed(d) -> bool:
            return bool(
                d.execute_script(
                    """
                    function vis(el) {
                        return !!(el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
                    }
                    var vf = document.getElementById('viewFiles');
                    var backdrops = document.querySelectorAll('.modal-backdrop');
                    var anyBackdrop = false;
                    for (var i = 0; i < backdrops.length; i++) {
                        if (vis(backdrops[i])) { anyBackdrop = true; break; }
                    }
                    if (!vis(vf) && !anyBackdrop) return true;
                    if (vis(vf)) {
                        var jq = window.jQuery;
                        var m = jq ? jq(vf).data('bs.modal') : null;
                        if (!m || (!m.isTransitioning && !m._isTransitioning)) {
                            var btn = vf.querySelector("button.close, [data-dismiss='modal']");
                            if (btn) btn.click();
                            else if (jq && jq.fn && jq.fn.modal) jq(vf).modal('hide');
                        }
                    }
                    return false;
                    """
                )
            )

        try:
            WebDriverWait(self.driver, 5, poll_frequency=0.1).until(_closed)
        except TimeoutException:
            try:
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Document Type, Metadata & Upload
    # ------------------------------------------------------------------

    def select_document_type(self, terms: list[str] | None = None) -> None:
        self.wait.until(EC.element_to_be_clickable(self.DOC_TYPE_BOX)).click()
        search_box = self.wait.until(EC.visibility_of_element_located(self.DOC_TYPE_SEARCH_BOX))
        search_box.click()
        for term in terms or cfg.DOC_TYPE_SEARCH_TERMS:
            typed = term.strip().strip("/").split("/")[-1]
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(
                Keys.BACKSPACE
            ).perform()
            for letter in typed:
                ActionChains(self.driver).send_keys(letter).perform()
                time.sleep(0.15)
            try:
                time.sleep(0.3)
                self.wait_for_ajax_idle(timeout=5)
                WebDriverWait(self.driver, 8).until(lambda _d: bool(self.select2_options(self.DOC_TYPE_OPTION)))
            except TimeoutException:
                continue
            self.wait_for_ajax_idle(timeout=5)
            options = self.select2_options(self.DOC_TYPE_OPTION)
            if options:
                index = self.best_option_index(options, term)
                option = options[index]
                print(f"   doc-type: picked '{option.get_attribute('title')}' (result {index + 1} of {len(options)})")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", option)
                ActionChains(self.driver).move_to_element(option).click().perform()
                self.wait_for_ajax_idle(timeout=5)
                selected = self.current_doc_type()
                if selected and "search for a document type" not in selected.lower():
                    return
                options = self.select2_options(self.DOC_TYPE_OPTION)
                if options:
                    opt = options[self.best_option_index(options, term)]
                    ActionChains(self.driver).move_to_element(opt).click().perform()
                    self.wait_for_ajax_idle(timeout=5)
                    return
        raise SetupError("document type could not be selected")

    def current_doc_type(self) -> str:
        el = self.driver.find_element(*self.DOC_TYPE_CONTAINER_TEXT)
        title = (el.get_attribute("title") or "").replace("×", "").strip()
        text = (el.text or "").replace("×", "").strip()
        if title and "search for" not in title.lower():
            return title
        return text

    def select_checker(self, preferred_checker: str | None = None) -> bool:
        checker_divs = self.driver.find_elements(*self.CHECKER_DIV)
        if not (checker_divs and checker_divs[0].is_displayed()):
            return False

        want = (preferred_checker or os.getenv("CHECKER_NAME") or cfg.USERNAME or "").strip()
        picked = self.driver.execute_script("""
            var div = document.getElementById('checker-div');
            if (!div || div.offsetParent === null) return '';
            var sel = div.querySelector('select') || document.getElementById('checker');
            if (!sel) return '';
            var want = (arguments[0] || '').toLowerCase();
            var chosen = null, valid = [];
            for (var i = 0; i < sel.options.length; i++) {
                var o = sel.options[i];
                var txt = (o.text || '').trim();
                if (!o.value || o.value === '0' || o.disabled || !txt || txt.toLowerCase().indexOf('select') === 0 || txt.toLowerCase() === 'none') continue;
                valid.push(o);
                if (want && (txt.toLowerCase() === want || txt.toLowerCase().indexOf(want) !== -1)) { chosen = o; break; }
            }
            if (!chosen && valid.length > 0) chosen = valid[0];
            if (!chosen) return '';
            sel.value = chosen.value;
            chosen.selected = true;
            if (window.$) {
                $(sel).val(chosen.value).trigger('change');
                if ($.fn.selectpicker) { $(sel).selectpicker('val', chosen.value).selectpicker('refresh'); }
            } else {
                sel.dispatchEvent(new Event('change', {bubbles: true}));
            }
            return chosen.text.trim();
        """, want)
        return bool(picked)

    def has_visible_checker(self) -> bool:
        divs = self.driver.find_elements(*self.CHECKER_DIV)
        return bool(divs and divs[0].is_displayed())

    def fill_metadata_form(self, terms: list[str] | None = None) -> None:
        self.select_document_type(terms)
        unique_num = random.randint(10000000, 99999999)
        run_id = f"{int(time.time()) % 100000}{random.randint(100, 999)}"

        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "#add_meta_data .meta-data-gen-wrap .form-group")) > 0
            )
        except TimeoutException:
            self.wait_for_ajax_idle(timeout=4)

        for attempt in range(3):
            try:
                panel = self.driver.find_element(*self.METADATA_PANEL)
                labels = panel.find_elements(By.XPATH, ".//label")
                for i, label in enumerate(labels):
                    ltext = label.text.lower().strip()
                    if not ltext or any(
                        k in ltext for k in ("document type", "share with", "file name", "tag", "checker")
                    ):
                        continue
                    is_required = "*" in label.text
                    try:
                        field = label.find_element(By.XPATH, self.FIELD_XPATH)
                    except Exception:
                        continue

                    if field.tag_name == "select":
                        if not is_required:
                            continue
                        self.driver.execute_script("""
                            var sel = arguments[0], valid = [];
                            for (var i = 0; i < sel.options.length; i++) {
                                var val = sel.options[i].value;
                                var txt = (sel.options[i].text || '').trim().toLowerCase();
                                if (val && !sel.options[i].disabled && txt !== 'none' && txt !== 'nothing selected') valid.push(sel.options[i]);
                            }
                            if (valid.length > 0) {
                                if (sel.multiple) {
                                    for (var k = 0; k < sel.options.length; k++) sel.options[k].selected = false;
                                    var shuffled = valid.slice().sort(function() { return Math.random() - 0.5; });
                                    var minC = valid.length >= 10 ? 5 : Math.min(2, valid.length);
                                    var maxC = valid.length >= 10 ? Math.min(10, valid.length - 2) : valid.length;
                                    var count = minC + Math.floor(Math.random() * Math.max(1, maxC - minC + 1));
                                    for (var j = 0; j < count; j++) shuffled[j].selected = true;
                                } else {
                                    var chosen = valid[Math.floor(Math.random() * valid.length)];
                                    chosen.selected = true;
                                    sel.value = chosen.value;
                                }
                                if (window.$) {
                                    $(sel).trigger('change');
                                    if ($.fn.selectpicker) $(sel).selectpicker('refresh');
                                }
                            }
                        """, field)
                        continue

                    if not field.is_displayed() or field.get_attribute("value"):
                        continue

                    field_id = (field.get_attribute("id") or "").lower()
                    field_type = (field.get_attribute("type") or "").lower()
                    outer_html = (field.get_attribute("outerHTML") or "").lower()

                    if "date" in field_id or "expires" in field_id:
                        if is_required:
                            field.send_keys(datetime.now().strftime("%Y-%m-%d"))
                    elif field_type == "number" or any(w in outer_html for w in ("digits", "number", "integer", "numeric")):
                        field.clear()
                        field.send_keys(str(unique_num + i))
                    else:
                        field.clear()
                        field.send_keys(f"AUTO_{run_id}_{i}")
                return
            except StaleElementReferenceException:
                if attempt == 2:
                    raise
                time.sleep(0.5)

    def set_document_name(self, name: str) -> str:
        field = self.driver.find_element(*self.FILE_NAME_INPUT)
        try:
            field.clear()
            field.send_keys(name)
        except Exception:
            pass
        return field.get_attribute("value") or ""

    def field_value(self, field_id: str) -> str:
        for _ in range(4):
            try:
                return self.driver.find_element(By.ID, field_id).get_attribute("value") or ""
            except StaleElementReferenceException:
                time.sleep(0.4)
        return ""

    def filled_values(self) -> list[tuple[str, str]]:
        for _ in range(4):
            try:
                pairs = []
                panel = self.driver.find_element(*self.METADATA_PANEL)
                for field in panel.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], textarea"):
                    value = field.get_attribute("value") or ""
                    if field.is_displayed() and value.startswith("AUTO_") and field.get_attribute("id") != "file_name":
                        try:
                            label = field.find_element(By.XPATH, "preceding::label[1]").text
                        except Exception:
                            label = ""
                        pairs.append((self.clean(label), value))
                return pairs
            except StaleElementReferenceException:
                time.sleep(0.4)
        return []

    def select_share(self, kind: str) -> str:
        def _share_option_ready(d) -> bool:
            if self.visible("#document_share_div #loaderOverlay"):
                return False
            return bool(d.execute_script("""
                var s = document.getElementById('shared_docs');
                if (!s) return false;
                var kind = (arguments[0] || '').toLowerCase();
                if (kind === 'public') return !!s.querySelector("option[value='all-1']");
                if (kind === 'all users') return !!s.querySelector("option[value='all-2']");
                var groups = s.querySelectorAll('optgroup');
                for (var i = 0; i < groups.length; i++) {
                    if ((groups[i].label || '').toLowerCase() === kind && groups[i].querySelector('option')) {
                        return true;
                    }
                }
                return false;
            """, kind))

        try:
            WebDriverWait(self.driver, 12).until(_share_option_ready)
        except TimeoutException:
            pass

        picked = self.driver.execute_script("""
            var s = document.getElementById('shared_docs'); var picked = '';
            var kind = (arguments[0] || '').toLowerCase();
            if (!s) return '';
            if (kind == 'public') { var o = s.querySelector("option[value='all-1']"); if (o) { o.selected = true; picked = o.text.trim(); } }
            else if (kind == 'all users') { var o = s.querySelector("option[value='all-2']"); if (o) { o.selected = true; picked = o.text.trim(); } }
            else {
                s.querySelectorAll('optgroup').forEach(function(g) {
                    if ((g.label || '').toLowerCase() == kind && !picked) {
                        var o = g.querySelector('option');
                        if (o) { o.selected = true; picked = o.text.trim(); }
                    }
                });
            }
            if (window.$) $(s).trigger('change');
            return picked;
        """, kind)
        if not picked:
            raise LookupError(f"no '{kind}' option in Share With")
        return picked

    def prepare_upload(
        self,
        ext: str = "pdf",
        doc_type: str | None = None,
        fill: bool = True,
        require_checker: bool = False,
        checker_name: str | None = None,
    ) -> str:
        sample = self.find_sample_file(ext)
        if not sample:
            raise SetupError(f"no .{ext} sample file in {cfg.SAMPLE_DIR}")
        try:
            _, copy_path = self.unique_copy(sample[1])
            pending_name = self.attach_new_file(copy_path) or self.attach_new_file(sample[1])
            if not pending_name:
                raise SetupError(
                    f"the system did not add '{sample[0]}' to the Pending Files list. "
                    f"Page said: {self.popup_text() or 'nothing'}"
                )
            self.open_pending_list()
            self.clear_selected_files()
            if self.selected_count():
                raise SetupError("files from an earlier run are still selected in Pending Documents")
            if not self.click_pending_icon(pending_name):
                info = self.pending_page_info()
                raise SetupError(
                    f"'{pending_name}' is in Pending Files but its icon could not be clicked (shows {info[0]} of {info[1]})"
                )
            WebDriverWait(self.driver, 5).until(lambda _d: self.selected_count() == 1)

            terms = [doc_type] if doc_type else cfg.DOC_TYPE_SEARCH_TERMS
            if fill:
                self.fill_metadata_form(terms)
                self.wait_for_ajax_idle(timeout=5)
                if require_checker and not self.has_visible_checker():
                    try:
                        WebDriverWait(self.driver, 6).until(lambda _d: self.has_visible_checker())
                    except TimeoutException:
                        pass
                checker_visible = self.has_visible_checker()
                if not require_checker and checker_visible:
                    raise SetupError(
                        f"Doc type '{self.current_doc_type()}' has Maker-Checker enabled; configure a non-checker DOC_TYPE"
                    )
                if require_checker and not checker_visible:
                    raise SetupError(
                        f"Doc type '{self.current_doc_type()}' (CHECKER_DOC_TYPE={doc_type!r}) "
                        f"does not have a Checker Group assigned (#checker-div is hidden)."
                    )
                if checker_visible:
                    try:
                        WebDriverWait(self.driver, 8).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#checker option")) > 1
                        )
                    except TimeoutException:
                        pass
                    if not self.select_checker(checker_name):
                        raise SetupError(
                            f"Checker dropdown (#checker-div) is shown for '{self.current_doc_type()}', "
                            f"but no checker could be selected."
                        )
            else:
                self.select_document_type(terms)
                self.wait_for_ajax_idle(timeout=5)
                if not require_checker and self.has_visible_checker():
                    raise SetupError(
                        f"Doc type '{self.current_doc_type()}' has Maker-Checker enabled; configure a non-checker DOC_TYPE"
                    )
        except SetupError:
            raise
        except Exception as exc:
            raise SetupError(f"could not prepare the upload ({type(exc).__name__}: {exc}) at {self.driver.current_url}") from exc
        return pending_name

    def click_save_upload(self) -> tuple[bool, str]:
        ok, message = self.message_after(lambda: self.click(self.driver.find_element(*self.UPLOAD_BTN)))
        if ok:
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda _d: self.selected_count() == 0
                    and not self.visible("#add_meta_data > #loaderOverlay")
                )
            except TimeoutException:
                if self.selected_count() > 0:
                    return False, f"upload did not clear pending selection ({message})"
        return ok, message

    def upload_document(
        self,
        ext: str = "pdf",
        doc_type: str | None = None,
        share: str | None = None,
        require_checker: bool = False,
        checker_name: str | None = None,
    ) -> dict:
        try:
            self.prepare_upload(
                ext,
                doc_type,
                require_checker=require_checker,
                checker_name=checker_name,
            )
            info = {"doc_type": self.current_doc_type(), "values": self.filled_values()}
            if share:
                info["shared_with"] = self.select_share(share)
            info["name"] = self.set_document_name(datetime.now().strftime("AUTO_%H%M%S"))
            ok, message = self.click_save_upload()
        except SetupError:
            raise
        except Exception as exc:
            raise SetupError(f"test document did not upload ({type(exc).__name__}: {exc})") from exc
        if not ok:
            raise SetupError(f"test document did not upload ({message})")
        self.wait_for_ajax_idle(timeout=5)
        return info

    def upload_with_values(
        self, doc_type: str, values: dict[str, str], doc_name: str | None = None
    ) -> tuple[bool, str]:
        """Upload a PDF to `doc_type` with explicit metadata field values."""
        self.prepare_upload("pdf", doc_type)
        for label, value in values.items():
            self.fill_field(label, value)
        self.set_document_name(doc_name or datetime.now().strftime("AUTO_%H%M%S%f"))
        return self.click_save_upload()

    # ------------------------------------------------------------------
    # Naming Convention Helpers (DMS-TC012)
    # ------------------------------------------------------------------

    def convention_of_selected_doc_type(self) -> str:
        value = (self.driver.execute_script("""
            try {
                var d = $('#DocumentType').select2('data')[0] || {};
                var c = d['data-convention'] || (d.element && d.element.dataset.convention) || d.document_name_convention || '';
                return Array.isArray(c) ? c.join(',') : String(c);
            } catch (e) { return ''; }
        """) or "").strip()
        return "" if value.strip("[]'\" ,") in ("", "null", "undefined") else value

    @staticmethod
    def convention_fields(convention: str) -> list[str]:
        names = []
        for part in convention.strip("[]'\" ").split(","):
            part = re.sub(r"\[\d+:\d+\]", "", part).strip()
            if part and part not in ("raw_filename", "upload_date", "_", "-") and re.search(r"[a-z]", part, re.I):
                names.append(part)
        return names

    def fill_convention_fields(self, fields: list[str]) -> None:
        run_id = datetime.now().strftime("%H%M%S")
        for i, name in enumerate(fields):
            for box in self.driver.find_elements(By.CSS_SELECTOR, f".meta-data-gen-wrap [name='{name}']"):
                kind = (box.get_attribute("type") or "text").lower()
                if not box.is_displayed() or box.tag_name not in ("input", "textarea") or box.get_attribute("value"):
                    continue
                if "date" in (box.get_attribute("class") or "") or kind == "date":
                    continue
                box.send_keys(str(int(run_id) + i) if kind == "number" else f"AUTO{run_id}{i}")

    def meta_values_excluding_dates(self) -> list[str]:
        for _ in range(3):
            try:
                values = []
                panel = self.driver.find_element(*self.METADATA_PANEL)
                for field in panel.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], textarea"):
                    field_id = (field.get_attribute("id") or "").lower()
                    value = field.get_attribute("value") or ""
                    if (
                        field.is_displayed()
                        and value
                        and field_id != "file_name"
                        and "date" not in field_id
                        and "expires" not in field_id
                    ):
                        values.append(value)
                return values
            except StaleElementReferenceException:
                time.sleep(0.4)
        return []

    def focus_file_name_for_convention(self) -> None:
        try:
            self.driver.find_element(*self.FILE_NAME_INPUT).click()
        except Exception:
            pass

    def form_field_values(self) -> tuple[dict[str, str], str]:
        panel = self.driver.find_element(*self.METADATA_PANEL)
        values: dict[str, str] = {}
        for el in panel.find_elements(
            By.CSS_SELECTOR, ".meta-data-gen-wrap [name], .locked-meta-data-gen-wrap-hidden [name]"
        ):
            name = (el.get_attribute("name") or "").strip()
            if name:
                values[name] = (el.get_attribute("value") or "").strip()
        created_date = ""
        cd = self.driver.find_elements(By.ID, "created_date")
        if cd:
            created_date = (cd[0].get_attribute("value") or "").strip()
        return values, created_date

    @staticmethod
    def expected_convention_name(
        pending_name: str,
        convention: str,
        field_values: dict[str, str],
        created_date: str = "",
    ) -> str:
        name_parts = pending_name.split(".")
        if len(name_parts) > 1:
            name_parts.pop()
        raw_no_ext = ",".join(name_parts).replace(",", ".", 1) if len(name_parts) > 1 else name_parts[0]
        raw_no_ext = os.path.splitext(pending_name)[0] if len(pending_name.split(".")) <= 2 else raw_no_ext

        out = []
        for raw_tok in convention.strip("[]'\" ").split(","):
            m = re.search(r"\[(\d+):(\d+)\]", raw_tok)
            clean_tok = re.sub(r"\[\d+:\d+\]", "", raw_tok).strip()
            if clean_tok == "raw_filename":
                val = raw_no_ext
            elif clean_tok == "upload_date":
                val = created_date
            elif clean_tok in field_values:
                val = field_values[clean_tok]
            else:
                val = clean_tok
            if m and val:
                val = val[int(m.group(1)) - 1:int(m.group(2))]
            out.append(val)
        return "".join(out)

    def wait_exact_file_name(self, expected_name: str, timeout: int = 10) -> tuple[bool, str]:
        try:
            WebDriverWait(self.driver, timeout).until(lambda _d: self.field_value("file_name") == expected_name)
            return True, self.field_value("file_name")
        except TimeoutException:
            return False, self.field_value("file_name")

    # ------------------------------------------------------------------
    # Watermarks (DMS-TC042, TC045, TC046, TC049, TC050)
    # ------------------------------------------------------------------

    def open_watermark_modal(self) -> None:
        modal = self.driver.find_element(*self.WATERMARK_MODAL)
        if not modal.is_displayed():
            self.click(self.wait.until(EC.element_to_be_clickable(self.WATERMARK_BTN)))
            self.wait.until(EC.visibility_of_element_located(self.WATERMARK_MODAL))
            self.wait_for_ajax_idle(timeout=5)

    def open_watermark_tab(self, tab_id: str) -> None:
        self.open_watermark_modal()
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, tab_id))))
        self.wait_for_ajax_idle(timeout=5)

    def _library_rows(self) -> list[str]:
        rows = self.driver.execute_script("""
            var c = document.getElementById('watermark_commonly_used_files_container');
            if (!c) return [];
            return Array.from(c.querySelectorAll('.list-group-item')).map(function(item) {
                var txt = (item.innerText || item.textContent || '').replace(/\\s+/g, ' ').trim();
                var vals = Array.from(item.querySelectorAll("input[name='watermark_file_check']")).map(function(cb) {
                    return cb.value || '';
                });
                return [txt].concat(vals).join(' ').trim();
            });
        """)
        return rows if isinstance(rows, list) else []

    def is_watermark_in_library(self, text: str) -> bool:
        self.open_watermark_tab(self.WATERMARK_LIBRARY_TAB)
        low = text.lower()
        try:
            WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda _d: any(low in r.lower() for r in self._library_rows())
            )
            return True
        except TimeoutException:
            return False

    def create_text_watermark(self, text: str) -> tuple[bool, str]:
        self.open_watermark_tab(self.WATERMARK_CUSTOM_TAB)
        box = self.wait.until(EC.visibility_of_element_located((By.ID, "watermark_text")))
        box.clear()
        box.send_keys(text)
        button = self.wait.until(EC.element_to_be_clickable((By.ID, "create_custom_text_watermark_button")))
        ok, message = self.message_after(lambda: self.click(button))
        if ok:
            self._created_watermarks.append(text)
        return ok, message

    def upload_watermark_file(self, path: str) -> tuple[bool, str]:
        self.open_watermark_tab(self.WATERMARK_UPLOAD_TAB)
        self.attach_to_file_input(path)
        button = self.wait.until(EC.element_to_be_clickable((By.ID, "submit-all")))
        ok, message = self.message_after(lambda: self.click(button))
        if ok:
            stem = os.path.splitext(os.path.basename(path))[0]
            self._created_watermarks.append(stem)
        return ok, message

    def search_watermark_library(self, wanted: str, other: str) -> tuple[bool, str]:
        self.open_watermark_tab(self.WATERMARK_LIBRARY_TAB)
        WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(
            lambda _d: any(wanted.lower() in r.lower() for r in self._library_rows())
        )
        box = self.wait.until(EC.element_to_be_clickable((By.ID, "watermark_files_search_box")))
        self.click(box)
        box.clear()
        if len(wanted) > 1:
            box.send_keys(wanted[:-1])
            self.wait_for_ajax_idle(timeout=8)
            box.send_keys(wanted[-1])
        else:
            box.send_keys(wanted)
        self.wait_for_ajax_idle(timeout=8)

        def _filtered(_d) -> bool:
            rows = self._library_rows()
            return (
                bool(rows)
                and all(wanted.lower() in r.lower() for r in rows)
                and not any(other.lower() in r.lower() for r in rows)
            )

        try:
            WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException,)).until(_filtered)
            rows = self._library_rows()
            return True, f"Search for '{wanted}' shows {len(rows)} matching row(s) and excludes '{other}'"
        except TimeoutException:
            rows = self._library_rows()
            return False, f"Search for '{wanted}' showed non-matching rows: {rows[:5]}"

    def attach_watermark_from_library(self, text: str) -> str:
        self.open_watermark_tab(self.WATERMARK_LIBRARY_TAB)
        checkbox_label = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//input[@name='watermark_file_check' and contains(@value, {self.xpath_text(text)})]/..")
            )
        )
        self.click(checkbox_label)
        attach = self.wait.until(EC.element_to_be_clickable((By.ID, "attachWatermarkFile")))
        self.click(attach)
        WebDriverWait(self.driver, 8).until(
            lambda d: bool(d.find_element(By.ID, "selected_watermark_name").text.strip())
        )
        return self.driver.find_element(By.ID, "selected_watermark_name").text.strip()

    def delete_watermark_from_library(self, text: str) -> tuple[bool, str]:
        self.open_watermark_tab(self.WATERMARK_LIBRARY_TAB)
        container = self.driver.find_element(*self.WATERMARK_LIBRARY_CONTAINER)
        icon_xpath = (
            f".//div[contains(@class,'list-group-item')][contains(., {self.xpath_text(text)})]"
            "//strong[contains(@class,'watermark-delete')]"
        )

        def _delete_it():
            icons = WebDriverWait(self.driver, 10).until(lambda _d: container.find_elements(By.XPATH, icon_xpath))
            self.click(icons[0])
            if not (self.confirm("delete") or self.confirm("yes")):
                raise AssertionError("Watermark delete confirmation modal did not appear")

        ok, message = self.message_after(_delete_it)
        if not ok:
            return False, message

        try:
            WebDriverWait(self.driver, 8).until(
                lambda _d: not any(text.lower() in r.lower() for r in self._library_rows())
            )
            gone = True
        except TimeoutException:
            gone = False
        if gone:
            self._created_watermarks = [w for w in self._created_watermarks if text.lower() not in w.lower()]
        return gone, f"{message}. Watermark " + ("removed from the library" if gone else "still shown in the library")

    def cleanup_created_watermarks(self) -> None:
        if not self._created_watermarks:
            return
        targets = list(dict.fromkeys(self._created_watermarks))
        self._created_watermarks.clear()
        if not (self.driver.current_url or "").startswith(cfg.BASE_URL):
            self.driver.get(cfg.PENDING_URL)
        self.driver.set_script_timeout(20)
        errors = self.driver.execute_async_script("""
            var cb = arguments[arguments.length - 1];
            var targets = arguments[0].map(s => String(s).toLowerCase());
            function getCookie(n) {
                var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)'));
                return m ? decodeURIComponent(m[1]) : '';
            }
            var csrf = (document.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value || getCookie('csrftoken') || '';
            (async () => {
                var errs = [];
                try {
                    for (var acc of [0, 1]) {
                        var res = await fetch('/api/v1/dms/documents/document_watermark/?accessible_by=' + acc);
                        if (!res.ok) continue;
                        var list = await res.json();
                        for (var item of (Array.isArray(list) ? list : [])) {
                            var blob = [item.file || '', item.custom_watermark_text || '', item.name || ''].join(' ').toLowerCase();
                            if (targets.some(t => blob.indexOf(t) !== -1)) {
                                var delRes = await fetch('/api/v1/dms/documents/document_watermark/' + item.id + '/', {
                                    method: 'DELETE',
                                    headers: {'X-CSRFToken': csrf}
                                });
                                if (!delRes.ok) errs.push(item.id + ': HTTP ' + delRes.status);
                            }
                        }
                    }
                } catch (e) { errs.push(String(e)); }
                cb(errs);
            })();
        """, targets)
        if errors:
            print(f"   [Warning] watermark cleanup errors: {errors}")
