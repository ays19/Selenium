"""Page Object for DMS Pending For Review (Maker-Checker) workflow."""
from __future__ import annotations

from datetime import date

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class ReviewPage(BasePage):
    """Encapsulates Pending For Review actions and Requested By Me / Checker filters."""

    TABLE = (By.ID, "pending-for-review")
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search_in_table")

    def open(self) -> None:
        self.driver.get(cfg.REVIEW_URL)
        self.wait_for_page_load()
        self.wait.until(EC.presence_of_element_located(self.TABLE))
        self.wait_for_ajax_idle(timeout=8)

    def default_user_filter(self) -> tuple[str, str]:
        self.open()
        val = self.driver.execute_script("return $('#select-user').val() || '';")
        label = self.driver.find_element(By.CSS_SELECTOR, "button[data-id='select-user'] .filter-option").text.strip()
        return str(val), label

    def select_user_scope(self, scope: str) -> None:
        self.pick_bootstrap_select("select-user", scope)
        self.wait_for_ajax_idle(timeout=8)

    def select_status(self, status: str) -> None:
        self.pick_bootstrap_select("select-status", status)
        self.wait_for_ajax_idle(timeout=8)

    def _pick_user_dropdown(self, select_id: str, div_id: str, name: str) -> str:
        WebDriverWait(self.driver, 10).until(lambda _d: bool(self.visible(f"#{div_id} button")))
        self.wait_for_ajax_idle(timeout=6)
        want = name.strip().lower()
        chosen = self.driver.execute_script("""
            var s = document.getElementById(arguments[0]);
            if (!s) return '';
            var want = arguments[1];
            var match = null;
            for (var i = 0; i < s.options.length; i++) {
                var o = s.options[i];
                var txt = (o.text || '').trim();
                if (!o.value) continue;
                if (!want || txt.toLowerCase().indexOf(want) !== -1) { match = o; break; }
            }
            if (!match) return '';
            $(s).selectpicker('val', match.value).trigger('change');
            return match.text.trim();
        """, select_id, want)
        if not chosen:
            raise SetupError(f"User matching '{name}' not found in #{select_id}")
        self.wait_for_ajax_idle(timeout=8)
        return chosen

    def select_checker_filter(self, checker_name: str) -> str:
        return self._pick_user_dropdown("select-checker", "select-checker-div", checker_name)

    def select_maker_filter(self, maker_name: str) -> str:
        return self._pick_user_dropdown("select-maker", "select-maker-div", maker_name)

    def select_doctype_filter(self, doc_type: str) -> None:
        self.pick_select2_by_id("doctype", doc_type)
        self.wait_for_ajax_idle(timeout=8)

    def clear_doctype_filter(self) -> None:
        self.driver.execute_script("$('#doctype').val(null).trigger('change');")
        self.wait_for_ajax_idle(timeout=6)

    def apply_date_range(self, field_id: str, start_ymd: str, end_ymd: str) -> None:
        WebDriverWait(self.driver, 8).until(EC.visibility_of_element_located((By.ID, field_id)))
        self.driver.execute_script("""
            var $f = $('#' + arguments[0]);
            var picker = $f.data('daterangepicker');
            picker.setStartDate(moment(arguments[1], 'YYYY-MM-DD'));
            picker.setEndDate(moment(arguments[2], 'YYYY-MM-DD'));
            $f.trigger('apply.daterangepicker', [picker]);
        """, field_id, start_ymd, end_ymd)
        self.wait_for_ajax_idle(timeout=8)

    def clear_date_range(self, field_id: str) -> None:
        self.driver.execute_script("""
            var $f = $('#' + arguments[0]);
            var picker = $f.data('daterangepicker');
            if (picker) $f.trigger('cancel.daterangepicker', [picker]);
            else $f.val('');
        """, field_id)
        self.wait_for_ajax_idle(timeout=8)

    def search_table(self, query: str) -> None:
        boxes = self.visible(self.SEARCH_INPUT[1])
        if boxes:
            boxes[0].clear()
            if query:
                boxes[0].send_keys(query)
            boxes[0].send_keys(Keys.ENTER)
            self.wait_for_ajax_idle(timeout=8)

    def _find_row(self, name: str, timeout: int = 10):
        self.search_table(name)
        low = name.lower()

        def _lookup(d):
            for tr in d.find_elements(By.CSS_SELECTOR, "#pending-for-review tbody tr"):
                if tr.is_displayed() and low in (tr.text or "").lower():
                    return tr
            return None

        try:
            return WebDriverWait(self.driver, timeout).until(_lookup)
        except TimeoutException:
            return None

    def table_contains(self, name: str, timeout: int = 8) -> bool:
        return self._find_row(name, timeout=timeout) is not None

    def review_document(self, name: str, action: str) -> tuple[bool, str]:
        """Open Pending For Review and approve/reject `name` via `.approve-doc` / `.reject-doc`."""
        self.open()
        row = self._find_row(name, timeout=10)
        if row is None:
            return False, f"document '{name}' not listed in Pending For Review"

        btn_cls = "a.approve-doc" if "approve" in action.lower() else "a.reject-doc"
        btns = [b for b in row.find_elements(By.CSS_SELECTOR, btn_cls) if b.is_displayed()]
        if not btns:
            return False, f"action button '{btn_cls}' not found for '{name}'"

        ok, msg = self.message_after(lambda: self.click(btns[0]))
        self.wait_for_ajax_idle(timeout=6)
        return ok, msg

    def has_checker_actions(self, name: str) -> tuple[bool, bool, bool]:
        """Check whether `name` is listed in current view with approve/reject buttons."""
        row = self._find_row(name, timeout=10)
        if row is None:
            return False, False, False
        approve = any(b.is_displayed() for b in row.find_elements(By.CSS_SELECTOR, "a.approve-doc"))
        reject = any(b.is_displayed() for b in row.find_elements(By.CSS_SELECTOR, "a.reject-doc"))
        return True, approve, reject

    def is_listed_in_requested_by_me(self, status: str, name: str) -> bool:
        self.open()
        self.select_user_scope("Requested By Me")
        self.select_status(status)
        return self.table_contains(name, timeout=6)

    def requested_by_me_statuses(self, name: str) -> list[bool]:
        return [
            self.is_listed_in_requested_by_me(status, name)
            for status in ("Pending", "Approved", "Rejected")
        ]

    @staticmethod
    def today_ymd() -> str:
        return date.today().strftime("%Y-%m-%d")
