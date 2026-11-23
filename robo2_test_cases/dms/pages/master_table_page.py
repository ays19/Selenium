"""Page Object for DMS Master Table Method (Fetch) settings and runtime fetch checks."""
from __future__ import annotations

from datetime import datetime
import os
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class MasterTablePage(BasePage):
    """Encapsulates Master Table Method CRUD, filtering, cloning, assignment, and fetch checks."""

    MTM_FORM = "#mtm_creation_main_form"

    _PICK_OPTION_JS = """
    var s = document.querySelector(arguments[0]);
    if (!s) return '';
    var want = (arguments[1] || '').trim().toLowerCase();
    var valid = [];
    for (var i = 0; i < s.options.length; i++) {
        var o = s.options[i];
        if (!o.disabled && o.value) valid.push(o);
    }
    if (!valid.length) return '';
    var chosen = null;
    if (!want) {
        chosen = valid[0];
    } else {
        for (var j = 0; j < valid.length; j++) {
            var o = valid[j];
            var txt = (o.text || '').trim().toLowerCase();
            var val = (o.value || '').trim().toLowerCase();
            var fn = (o.dataset && o.dataset.field_name ? o.dataset.field_name : '').trim().toLowerCase();
            var ft = (o.dataset && o.dataset.field_title ? o.dataset.field_title : '').trim().toLowerCase();
            if (txt === want || val === want || fn === want || ft === want) { chosen = o; break; }
        }
        if (!chosen) {
            for (var k = 0; k < valid.length; k++) {
                var o = valid[k];
                var txt = (o.text || '').trim().toLowerCase();
                var val = (o.value || '').trim().toLowerCase();
                var fn = (o.dataset && o.dataset.field_name ? o.dataset.field_name : '').trim().toLowerCase();
                var ft = (o.dataset && o.dataset.field_title ? o.dataset.field_title : '').trim().toLowerCase();
                if (txt.indexOf(want) !== -1 || val.indexOf(want) !== -1 || fn.indexOf(want) !== -1 || ft.indexOf(want) !== -1) {
                    chosen = o; break;
                }
            }
        }
    }
    if (!chosen) return '';
    s.value = chosen.value;
    if (window.$) {
        $(s).trigger('change');
        if ($.fn.selectpicker) $(s).selectpicker('refresh');
    } else {
        s.dispatchEvent(new Event('change', {bubbles: true}));
    }
    return chosen.text.trim();
    """

    _LIST_TABLES_JS = """
    return Array.from(document.querySelectorAll(arguments[0] + ' select[name="master_table"] option'))
        .filter(function(o) { return o.value && !o.disabled; })
        .map(function(o) { return o.text.trim(); });
    """

    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self._created_method_names: list[str] = []
        self._created_method_ids: list[int] = []
        self._last_clone_pair: tuple[int | None, int | None] = (None, None)

    def open(self) -> None:
        self.driver.get(cfg.MASTER_TABLE_URL)
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            lambda _d: bool(self.visible(".mtm-list-card, .MTM-empty-card"))
        )
        self.wait_for_ajax_idle(timeout=5)

    def _api_list_methods(self, keyword: str = "", limit: int = 100) -> list[dict]:
        """List methods via MTM backend API for reliable ID tracking and cleanup."""
        self.driver.set_script_timeout(20)
        res = self.driver.execute_async_script("""
            var cb = arguments[arguments.length - 1];
            var kw = arguments[0] || '';
            var lim = arguments[1] || 100;
            var qs = 'show=all&offset=0&limit=' + encodeURIComponent(lim);
            if (kw) qs += '&method_search_keyword=' + encodeURIComponent(kw);
            fetch('/dms/master-table-method-dms/method-dms/?' + qs)
                .then(r => r.json())
                .then(d => cb((d && d.results) ? d.results : []))
                .catch(() => cb([]));
        """, keyword, limit)
        return res if isinstance(res, list) else []

    def cleanup_created_methods(self) -> None:
        """Delete any AUTO_MT_* methods created/cloned/assigned during this session."""
        if not self._created_method_names and not self._created_method_ids:
            return
        names = list(dict.fromkeys(self._created_method_names))
        ids = list(dict.fromkeys(self._created_method_ids))
        self._created_method_names.clear()
        self._created_method_ids.clear()
        try:
            if not (self.driver.current_url or "").startswith(cfg.BASE_URL):
                self.open()
            elif "/master-table-method" not in (self.driver.current_url or "").lower():
                self.driver.get(cfg.MASTER_TABLE_URL)
                self.wait_for_page_load()

            self.driver.set_script_timeout(30)
            res = self.driver.execute_async_script("""
                var cb = arguments[arguments.length - 1];
                var targetNames = arguments[0] || [];
                var explicitIds = arguments[1] || [];
                function getCookie(n) {
                    var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)'));
                    return m ? decodeURIComponent(m[1]) : '';
                }
                var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
                var csrf = (el && el.value) || getCookie('csrftoken') || '';
                (async () => {
                    try {
                        var resp = await fetch('/dms/master-table-method-dms/method-dms/?show=all&method_search_keyword=AUTO_MT_&offset=0&limit=100');
                        var data = await resp.json();
                        var results = Array.isArray(data.results) ? data.results : [];
                        var existingIds = new Set(results.map(function(item) { return Number(item.id); }));
                        var idSet = new Set();
                        explicitIds.forEach(function(eid) {
                            var num = Number(eid);
                            if (existingIds.has(num)) idSet.add(num);
                        });
                        results.forEach(function(item) {
                            var mname = (item.method_name || (item.method && item.method.name) || '').trim();
                            if (!mname) return;
                            for (var i = 0; i < targetNames.length; i++) {
                                var tn = targetNames[i];
                                if (mname === tn || mname.indexOf(tn) === 0) {
                                    idSet.add(Number(item.id));
                                    break;
                                }
                            }
                        });
                        var idsToDelete = Array.from(idSet).filter(function(x) { return !isNaN(x) && x > 0; });
                        if (!idsToDelete.length) {
                            cb({ok: true, deleted: 0});
                            return;
                        }
                        var delResp = await fetch('/dms/master-table-method-dms/method-dms/delete_methods/', {
                            method: 'DELETE',
                            headers: {'X-CSRFToken': csrf, 'Content-Type': 'application/json'},
                            body: JSON.stringify({method_ids: idsToDelete})
                        });
                        cb({ok: delResp.ok, status: delResp.status, deleted: idsToDelete.length});
                    } catch (e) {
                        cb({ok: false, error: String(e)});
                    }
                })();
            """, names, ids)
            if isinstance(res, dict) and not res.get("ok"):
                print(f"   [Warning] master_table cleanup returned non-OK: {res}")
        except Exception as exc:
            print(f"   [Warning] master_table cleanup error: {exc}")

    @staticmethod
    def _card_xpath_by_id(mtm_id: int) -> str:
        return (
            f"//div[contains(concat(' ', normalize-space(@class), ' '), ' mtm-list-card ')"
            f" and @data-mtm_id='{int(mtm_id)}']"
        )

    def _card_xpath(self, name: str) -> str:
        return (
            f"//div[contains(concat(' ', normalize-space(@class), ' '), ' mtm-list-card ')"
            f" and .//span[@title={self.xpath_text(name)}]]"
        )

    def _locate_card(self, name: str, mtm_id: int | None = None):
        card_xpath = self._card_xpath_by_id(mtm_id) if mtm_id is not None else self._card_xpath(name)
        cards = [c for c in self.driver.find_elements(By.XPATH, card_xpath) if c.is_displayed()]
        if cards:
            return card_xpath, cards[0]
        self.open()
        cards = [c for c in self.driver.find_elements(By.XPATH, card_xpath) if c.is_displayed()]
        if cards:
            return card_xpath, cards[0]
        if name:
            search_boxes = self.visible("input.method_search_input")
            if search_boxes:
                search_boxes[0].click()
                search_boxes[0].clear()
                search_boxes[0].send_keys(name, Keys.ENTER)
                self.wait_for_ajax_idle(timeout=6)
        card = WebDriverWait(self.driver, 10).until(
            lambda d: next((c for c in d.find_elements(By.XPATH, card_xpath) if c.is_displayed()), None)
        )
        return card_xpath, card

    def _open_card_action(self, name: str, button_css: str, mtm_id: int | None = None):
        """Find a method card (optionally by ID), expand its gear if needed, return (card_xpath, button)."""
        try:
            card_xpath, card = self._locate_card(name, mtm_id=mtm_id)
            button = card.find_element(By.CSS_SELECTOR, button_css)
            if not button.is_displayed():
                self.click(card.find_element(By.CSS_SELECTOR, "a.mtm_setting_button"))
                WebDriverWait(self.driver, 5).until(lambda _d: button.is_displayed())
            return card_xpath, button
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' (id={mtm_id}) was not found in the method list") from exc

    # ------------------------------------------------------------------
    # Form Field Selection & Creation
    # ------------------------------------------------------------------

    def mtm_choose(self, name: str, want: str | None = None, seconds: int = 10) -> str:
        css = f'{self.MTM_FORM} select[name="{name}"]'
        try:
            return WebDriverWait(self.driver, seconds, poll_frequency=0.5).until(
                lambda d: d.execute_script(self._PICK_OPTION_JS, css, want or "")
            )
        except TimeoutException as exc:
            suffix = f" '{want}'" if want else ""
            raise SetupError(f"the '{name}' drop-down of the method form has no option{suffix}") from exc

    def mtm_field_visible(self, name: str) -> bool:
        return bool(
            self.driver.execute_script(
                "var s = document.querySelector(arguments[0]); var box = s && s.closest('.col-container'); "
                "return !!box && box.offsetParent !== null;",
                f'{self.MTM_FORM} select[name="{name}"]',
            )
        )

    def mtm_pick_master_table(self, wanted: str | None = None) -> str:
        wanted = (wanted or os.getenv("MTM_MASTER_TABLE") or "Maverick").strip()
        if wanted:
            return self.mtm_choose("master_table", wanted)
        names = self.driver.execute_script(self._LIST_TABLES_JS, self.MTM_FORM)
        for name in names[:15]:
            self.mtm_choose("master_table", name)
            try:
                self.mtm_choose("mtm_match_criteria_mt_field", seconds=4)
                return name
            except SetupError:
                continue
        raise SetupError("no master table with fields was found for the method")

    def _type_and_pick_select2(self, box_css: str, search_css: str, option_css: str, term: str) -> str:
        search = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, search_css)))
        search.click()
        typed = term.strip().strip("/").split("/")[-1]
        for letter in typed[:30]:
            search.send_keys(letter)
            time.sleep(0.15)
        WebDriverWait(self.driver, 15).until(lambda _d: bool(self.select2_options(option_css)))
        self.wait_for_ajax_idle(timeout=5)
        options = self.select2_options(option_css)
        option = options[self.best_option_index(options, term)]
        chosen_text = option.text.strip()
        ActionChains(self.driver).move_to_element(option).click().perform()
        self.wait_for_ajax_idle(timeout=4)
        return chosen_text

    def mtm_pick_doc_type(self, term: str) -> None:
        box = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"{self.MTM_FORM} .method_form_document_type-container span.select2-selection")
            )
        )
        self.click(box)
        self._type_and_pick_select2(
            f"{self.MTM_FORM} .method_form_document_type-container",
            ".select2-container--open input.select2-search__field",
            ".select2-container--open .select2-results__option",
            term,
        )
        shown = self.driver.find_element(
            By.CSS_SELECTOR, f"{self.MTM_FORM} .method_form_document_type-container .select2-selection__rendered"
        ).text.lower()
        if not shown.strip() or "select document type" in shown:
            raise SetupError(f"document type '{term}' could not be selected in the method form")

    def create_method(
        self,
        record_type: str = "multiple record",
        doc_type: str | None = None,
        master_table: str | None = None,
        criteria_mt_field: str = "Name",
        criteria_operator: str = "EQUAL",
        criteria_meta_field: str = "name",
        populate_mt_field: str = "Age",
        populate_meta_field: str | None = None,
    ) -> tuple[bool, str, str]:
        is_multiple = "multiple" in record_type.lower()
        doc_type = (doc_type or os.getenv("MTM_DOC_TYPE") or "/Chelsea/").strip() or "/Chelsea/"
        master_table = (master_table or os.getenv("MTM_MASTER_TABLE") or "Maverick").strip() or "Maverick"
        populate_meta_field = populate_meta_field or ("month" if is_multiple else "salary")

        self.open()
        add_buttons = self.visible("#dms_method_add")
        if add_buttons:
            self.click(add_buttons[0])
        else:
            self.click_label("add method")
        self.wait.until(EC.visibility_of_element_located((By.ID, "mtm_creation_main_form")))
        self.wait_for_ajax_idle(timeout=4)

        name = datetime.now().strftime("AUTO_MT_%H%M%S%f")[:18]
        title_box = self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]')
        title_box.clear()
        title_box.send_keys(name)
        try:
            self.mtm_pick_master_table(master_table)
            self.mtm_pick_doc_type(doc_type)
            self.mtm_choose("mtm_output_type", "multiple" if is_multiple else "single")
            self.wait_for_ajax_idle(timeout=4)
            for field in ("mtm_fetch_all_record", "mtm_unique_fetch_record"):
                if self.mtm_field_visible(field):
                    self.mtm_choose(field, "false")
            self.mtm_choose("mtm_match_criteria_mt_field", criteria_mt_field)
            self.mtm_choose("mtm_match_criteria_operator", criteria_operator)
            self.mtm_choose("mtm_match_criteria_value_type", "meta_data_field")
            self.mtm_choose("mtm_match_criteria_metadata_field", criteria_meta_field)
            self.mtm_choose("mtm_populate_mt_field", populate_mt_field)
            self.mtm_choose("mtm_populate_metadata_field", populate_meta_field)
            save = self.driver.find_element(By.ID, "save_mtm_dms")
            ok, message = self.message_after(lambda: self.click(save))
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' was not saved. The form says: {self.form_problems() or 'nothing'}") from exc

        if ok:
            self._created_method_names.append(name)
            try:
                _xp, card = self._locate_card(name)
                mid = card.get_attribute("data-mtm_id")
                if mid and str(mid).isdigit():
                    self._created_method_ids.append(int(mid))
                listed = True
            except SetupError:
                listed = False
            if not listed:
                return False, f"{message}, but method '{name}' did not appear in the method list", name
        return ok, message, name

    def new_method(self, record_type: str = "multiple record", **kwargs) -> str:
        ok, message, name = self.create_method(record_type, **kwargs)
        if not ok:
            raise SetupError(f"master table method could not be created ({message})")
        return name

    # ------------------------------------------------------------------
    # Update, Delete, Enable/Disable, Clone, Filter, Search, Assign
    # ------------------------------------------------------------------

    def _wait_form_populated(self, expected_name: str = "") -> None:
        self.wait.until(EC.visibility_of_element_located((By.ID, "mtm_creation_main_form")))
        if expected_name:
            title = self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]')
            WebDriverWait(self.driver, 15).until(lambda _d: title.get_attribute("value") == expected_name)
        WebDriverWait(self.driver, 15).until(
            lambda d: d.execute_script(
                "var s = document.querySelector(arguments[0]); return !!s && !!s.value;",
                f'{self.MTM_FORM} select[name="mtm_populate_metadata_field"]',
            )
        )
        self.wait_for_ajax_idle(timeout=4)

    def update_method(
        self,
        name: str,
        new_name: str,
        populate_mt_field: str | None = None,
        populate_meta_field: str | None = None,
    ) -> tuple[bool, str]:
        try:
            _xp, card = self._locate_card(name)
            self.click(card.find_element(By.CSS_SELECTOR, "a.mtm_edit_button"))
            self._wait_form_populated(expected_name=name)
        except TimeoutException as exc:
            raise SetupError(f"the edit form of method '{name}' did not open or fill in") from exc

        title = self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]')
        title.clear()
        title.send_keys(new_name)
        if populate_mt_field:
            self.mtm_choose("mtm_populate_mt_field", populate_mt_field)
        if populate_meta_field:
            self.mtm_choose("mtm_populate_metadata_field", populate_meta_field)
        try:
            save = self.driver.find_element(By.ID, "save_mtm_dms")
            ok, message = self.message_after(lambda: self.click(save))
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' was not updated. The form says: {self.form_problems() or 'nothing'}") from exc

        if ok:
            self._created_method_names.append(new_name)
        listed = self.wait_text(new_name, 8)
        if not listed and ok:
            try:
                self._locate_card(new_name)
                listed = True
            except SetupError:
                listed = False
        return ok and listed, message + ("" if listed else f". '{new_name}' is not in the method list")

    def delete_method(self, name: str, mtm_id: int | None = None) -> tuple[bool, str]:
        card_xpath, button = self._open_card_action(name, "button.mtm_delete_button", mtm_id=mtm_id)

        def _action():
            self.click(button)
            if not self.confirm("yes", seconds=15):
                raise AssertionError("Confirmation modal ('Yes, delete it!') did not appear for method deletion")

        ok, message = self.message_after(_action)
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: not any(e.is_displayed() for e in d.find_elements(By.XPATH, card_xpath))
            )
            gone = True
        except TimeoutException:
            gone = False
        if ok and gone:
            self._created_method_names = [n for n in self._created_method_names if n != name]
            if mtm_id is not None:
                self._created_method_ids = [i for i in self._created_method_ids if i != int(mtm_id)]
        return ok and gone, message + (". Method removed from the list" if gone else ". Method still shown in the list")

    def set_method_disabled(self, name: str, target_disabled: bool, mtm_id: int | None = None) -> tuple[bool, str]:
        """Toggle Disable/Enable on a method card, await the 1s reload, and verify `data-mtm-disabled`."""
        card_xpath, button = self._open_card_action(name, "button.mtm_disable_button", mtm_id=mtm_id)
        old_html = self.driver.find_element(By.TAG_NAME, "html")

        ok, message = self.message_after(lambda: self.click(button))
        if not ok:
            return False, message

        try:
            WebDriverWait(self.driver, 8).until(EC.staleness_of(old_html))
        except TimeoutException:
            self.open()
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            lambda _d: bool(self.visible(".mtm-list-card, .MTM-empty-card"))
        )
        self.wait_for_ajax_idle(timeout=5)

        expected_attr = "true" if target_disabled else "false"
        try:
            _xp, card = self._locate_card(name, mtm_id=mtm_id)
            actual_attr = (card.get_attribute("data-mtm-disabled") or "").lower()
            state_ok = actual_attr == expected_attr
        except SetupError:
            actual_attr = "missing"
            state_ok = False
        return ok and state_ok, f"{message} (data-mtm-disabled='{actual_attr}', expected='{expected_attr}')"

    def clone_method(self, name: str) -> tuple[bool, str, str]:
        """Clone a method card via direct API toast + list reload, returning (ok, message, clone_name)."""
        card_xpath, button = self._open_card_action(name, "button.mtm_clone_button")
        card = self.driver.find_element(By.XPATH, card_xpath)
        orig_id_raw = card.get_attribute("data-mtm_id")
        orig_id = int(orig_id_raw) if orig_id_raw and str(orig_id_raw).isdigit() else None

        before_methods = self._api_list_methods(limit=50)
        before_ids = {int(m["id"]) for m in before_methods if m.get("id")}

        ok, message = self.message_after(lambda: self.click(button))
        if not ok:
            return False, message, ""

        time.sleep(1.5)
        self.wait_for_ajax_idle(timeout=6)

        new_entry = None
        for _ in range(5):
            after_methods = self._api_list_methods(limit=50)
            added = [m for m in after_methods if m.get("id") and int(m["id"]) not in before_ids]
            if added:
                new_entry = added[0]
                break
            time.sleep(0.5)

        if not new_entry:
            return False, f"{message}, but cloned method was not found in the method list", ""

        new_id = int(new_entry["id"])
        cloned_name = (
            new_entry.get("method_name")
            or (new_entry.get("method") or {}).get("name")
            or name
        ).strip()
        self._created_method_ids.append(new_id)
        if cloned_name:
            self._created_method_names.append(cloned_name)
        self._last_clone_pair = (orig_id, new_id)
        return True, f"{message} (cloned '{name}' -> '{cloned_name}' id={new_id})", cloned_name

    def filter_by_doc_type(self, doc_type: str, expected_method: str | None = None) -> tuple[bool, str]:
        self.open()
        box = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".MTM-doctype_method span.select2-selection"))
        )
        self.click(box)
        chosen = self._type_and_pick_select2(
            ".MTM-doctype_method",
            ".select2-container--open input.select2-search__field",
            "#select2-doctype_method-results .select2-results__option",
            doc_type,
        )
        self.wait_for_ajax_idle(timeout=6)

        cards = self.visible(".method-list-card-container .mtm-list-card")
        doc_types_shown = []
        shown_names = []
        for card in cards:
            dt_spans = card.find_elements(By.CSS_SELECTOR, ".summary-item i[title='Document Type'] + span")
            doc_types_shown.append(dt_spans[0].text.strip() if dt_spans else card.text.strip())
            m_spans = card.find_elements(By.CSS_SELECTOR, ".summary-item i[title='Method'] + span")
            if m_spans:
                shown_names.append(m_spans[0].text.strip())

        target = chosen.strip().strip("/").split("/")[-1].lower()
        wrong = [dt for dt in doc_types_shown if target not in dt.lower()]
        expected_ok = True if not expected_method else (expected_method in shown_names)
        ok = bool(cards) and not wrong and expected_ok
        details = f"Filter '{chosen}' shows {len(cards)} method(s)"
        if wrong:
            details += f", {len(wrong)} of them do not belong to '{chosen}'"
        if not expected_ok:
            details += f", expected method '{expected_method}' was missing"
        return ok, details

    def search_method(self, query: str, by: str = "method") -> tuple[bool, str]:
        self.open()
        search_box = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input.method_search_input"))
        )
        search_box.click()
        search_box.clear()
        search_box.send_keys(query, Keys.ENTER)
        self.wait_for_ajax_idle(timeout=6)
        try:
            WebDriverWait(self.driver, 8).until(
                lambda _d: bool(self.visible(".method-list-card-container .mtm-list-card"))
                or bool(self.visible(".MTM-empty-card"))
            )
        except TimeoutException:
            pass

        cards = self.visible(".method-list-card-container .mtm-list-card")
        icon_title = "Table" if by == "table" else "Method"
        shown_values = []
        for card in cards:
            spans = card.find_elements(By.CSS_SELECTOR, f".summary-item i[title='{icon_title}'] + span")
            shown_values.append(spans[0].text.strip() if spans else card.text.strip())

        wrong = [v for v in shown_values if query.lower() not in v.lower()]
        ok = bool(cards) and not wrong
        return ok, f"Search by {by} '{query}' shows {len(cards)} method(s)" + ("" if ok else f", {len(wrong)} do not match ({shown_values[:3]})")

    def assign_method(self, name: str, doc_type: str) -> tuple[bool, str]:
        """Assign `name` to `doc_type` and assert green success feedback inside #doc_type_assign_error_div."""
        _card_xpath, button = self._open_card_action(name, "button.mtm_assign_button")
        assign_box = "#method_assign_to_document_type_parent"

        self.click(button)
        self.wait.until(EC.visibility_of_element_located((By.ID, "on_assign_method_doc_type_modal")))
        self.wait_for_ajax_idle(timeout=4)
        self._type_and_pick_select2(
            assign_box,
            f"{assign_box} input.select2-search__field",
            ".select2-container--open .select2-results__option",
            doc_type.strip(),
        )
        if not self.driver.find_elements(By.CSS_SELECTOR, f"{assign_box} li.select2-selection__choice"):
            raise SetupError(f"document type '{doc_type}' could not be selected in the Assign To box")

        self.click(self.driver.find_element(By.ID, "on_assign_method_doc_type_modal_form_save_btn"))
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: bool(d.find_elements(By.CSS_SELECTOR, "#doc_type_assign_error_div li"))
                or bool(self.visible("[data-notify='container'], .toast-message"))
            )
        except TimeoutException as exc:
            raise SetupError(f"no confirmation or error message appeared after assigning '{name}' -> '{doc_type}'") from exc

        feedback = self.driver.execute_script("""
            var items = Array.from(document.querySelectorAll('#doc_type_assign_error_div li'));
            var green = [], red = [], other = [];
            items.forEach(function(li) {
                var col = (li.style.color || '').toLowerCase();
                var txt = (li.textContent || '').trim();
                if (!txt) return;
                if (col.indexOf('green') !== -1) green.push(txt);
                else if (col.indexOf('red') !== -1) red.push(txt);
                else other.push(txt);
            });
            return {green: green, red: red, other: other};
        """) or {"green": [], "red": [], "other": []}

        close_btns = self.visible("#on_assign_method_doc_type_modal button.close, #on_assign_method_doc_type_modal [data-dismiss='modal']")
        if close_btns:
            self.click(close_btns[0])
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.ID, "on_assign_method_doc_type_modal"))
                )
            except TimeoutException:
                pass

        self._created_method_names.append(name)
        green = feedback.get("green", [])
        red = feedback.get("red", [])
        ok = len(green) >= 1 and len(red) == 0
        summary = f"green={green}, red={red}"
        return ok, f"Assign '{name}' -> '{doc_type}' result: {summary}"

    # ------------------------------------------------------------------
    # Runtime Fetch Verification Across Upload, Edit, Adv Search, Explorer
    # ------------------------------------------------------------------

    def _trigger_and_read_populated(
        self,
        root_css: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
        is_explorer: bool = False,
    ) -> tuple[bool, str]:
        is_multiple = "multiple" in output_type.lower()
        criteria_css = f"{root_css} input[name='{criteria_field}']"
        try:
            field = WebDriverWait(self.driver, 10).until(
                lambda d: next((e for e in d.find_elements(By.CSS_SELECTOR, criteria_css) if e.is_displayed()), None)
            )
        except TimeoutException:
            return False, f"criteria field '{criteria_field}' not visible under {root_css}"

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.BACKSPACE)
        field.send_keys(criteria_value)
        time.sleep(0.1)
        field.send_keys(Keys.ENTER)

        if is_explorer:
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: (d.execute_script("return window.__dmsExplorerMtmExecutePending || 0;") == 0)
                )
            except TimeoutException:
                pass
        self.wait_for_ajax_idle(timeout=6)

        if is_multiple:
            pop_css = f"{root_css} select[name='{populate_field}']"

            def _read_options() -> list[str]:
                pairs = self.driver.execute_script("""
                    var sel = document.querySelector(arguments[0]);
                    if (!sel) return null;
                    var out = [];
                    for (var i = 0; i < sel.options.length; i++) {
                        var v = (sel.options[i].value || '').trim();
                        var t = (sel.options[i].text || '').trim();
                        if (!v && (!t || t.toLowerCase() === 'none' || t.toLowerCase() === 'nothing selected')) continue;
                        if (t) out.push(t);
                        if (v && v !== t) out.push(v);
                    }
                    return out;
                """, pop_css)
                return pairs if isinstance(pairs, list) else []

            if expect_present:
                try:
                    WebDriverWait(self.driver, 8).until(
                        lambda _d: expected_value.lower() in [o.lower() for o in _read_options()]
                    )
                    return True, f"dropdown '{populate_field}' populated option '{expected_value}'"
                except TimeoutException:
                    return False, f"dropdown '{populate_field}' did not receive '{expected_value}' (options={_read_options()[:8]})"
            else:
                time.sleep(1.5)
                self.wait_for_ajax_idle(timeout=4)
                opts = _read_options()
                found = expected_value.lower() in [o.lower() for o in opts]
                return (not found), (
                    f"dropdown '{populate_field}' does not have '{expected_value}'"
                    if not found
                    else f"dropdown '{populate_field}' STILL populated '{expected_value}' (options={opts[:8]})"
                )

        single_css = (
            f"{root_css} input[name='{populate_field}'], "
            f"{root_css} textarea[name='{populate_field}'], "
            f"{root_css} select[name='{populate_field}']"
        )

        def _read_single() -> str:
            return (self.driver.execute_script("""
                var el = document.querySelector(arguments[0]);
                return el ? String(el.value || '').trim() : '';
            """, single_css) or "").strip()

        if expect_present:
            try:
                WebDriverWait(self.driver, 8).until(lambda _d: _read_single().lower() == expected_value.lower())
                return True, f"field '{populate_field}' fetched '{_read_single()}'"
            except TimeoutException:
                return False, f"field '{populate_field}' value '{_read_single()}' != expected '{expected_value}'"
        else:
            time.sleep(1.5)
            self.wait_for_ajax_idle(timeout=4)
            actual = _read_single()
            still_fetched = actual.lower() == expected_value.lower()
            return (not still_fetched), (
                f"field '{populate_field}' remained '{actual}' (not fetched)"
                if not still_fetched
                else f"field '{populate_field}' STILL fetched '{actual}'"
            )

    def verify_fetch_in_upload(
        self,
        upload_page,
        doc_type: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
    ) -> tuple[bool, str]:
        """Verify MTM fetch (positive or negative) in Pending -> Add Meta Data panel."""
        upload_page.open_pending_list()
        pending_name = next(
            (
                r.get_attribute("data-pending-doc-name")
                for r in self.driver.find_elements(*upload_page.PENDING_ROW)
                if r.is_displayed() and r.get_attribute("data-pending-doc-name")
            ),
            None,
        )
        if not pending_name:
            sample = upload_page.find_sample_file("pdf")
            if not sample:
                raise SetupError("no sample PDF available to test Upload MTM fetch")
            _, copy_path = upload_page.unique_copy(sample[1])
            pending_name = upload_page.attach_new_file(copy_path) or upload_page.attach_new_file(sample[1])
            if not pending_name:
                raise SetupError("failed to attach sample PDF for Upload MTM fetch test")
            upload_page.open_pending_list()

        upload_page.clear_selected_files()
        if not upload_page.click_pending_icon(pending_name):
            raise SetupError(f"could not select pending file '{pending_name}'")
        WebDriverWait(self.driver, 5).until(lambda _d: upload_page.selected_count() == 1)
        upload_page.select_document_type([doc_type])
        WebDriverWait(self.driver, 10).until(
            lambda _d: bool(
                self.visible(
                    "#add_meta_data .meta-data-gen-wrap input, #add_meta_data .meta-data-gen-wrap select, "
                    "#add_meta_data .locked-meta-data-gen-wrap input, #add_meta_data .locked-meta-data-gen-wrap select"
                )
            )
        )
        self.wait_for_ajax_idle(timeout=6)
        time.sleep(0.3)
        ok, msg = self._trigger_and_read_populated(
            "#add_meta_data",
            criteria_field,
            criteria_value,
            populate_field,
            output_type,
            expected_value,
            expect_present=expect_present,
        )
        return ok, f"Upload: {msg}"

    def verify_fetch_in_edit_metadata(
        self,
        explorer_page,
        doc_name: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
    ) -> tuple[bool, str]:
        """Verify MTM fetch in Document View -> Edit Metadata modal."""
        main_tab = self.driver.current_window_handle
        try:
            explorer_page.open_document(doc_name)
            edit_btn = explorer_page.find_by_label("edit metadata")
            if edit_btn is not None:
                self.click(edit_btn)
            else:
                btns = self.visible("button[data-target='#editMeta'], a[data-target='#editMeta'], #editMetaBtn")
                if not btns:
                    return False, "Edit Metadata: Edit button not found on Document View"
                self.click(btns[0])

            self.wait.until(EC.visibility_of_element_located((By.ID, "editMeta")))
            WebDriverWait(self.driver, 12).until(
                lambda _d: bool(
                    self.visible(
                        "#editMeta .meta-data-gen-wrap input, #editMeta .meta-data-gen-wrap select, "
                        "#editMeta .locked-meta-data-gen-wrap input, #editMeta .locked-meta-data-gen-wrap select"
                    )
                )
                and not self.visible("#updateMetadataForm #loaderOverlay")
            )
            self.wait_for_ajax_idle(timeout=6)
            time.sleep(0.3)
            ok, msg = self._trigger_and_read_populated(
                "#editMeta",
                criteria_field,
                criteria_value,
                populate_field,
                output_type,
                expected_value,
                expect_present=expect_present,
            )
            return ok, f"Edit Metadata: {msg}"
        finally:
            self.close_extra_tabs(main_tab)

    def verify_fetch_in_advanced_search(
        self,
        explorer_page,
        doc_type: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
    ) -> tuple[bool, str]:
        """Verify MTM fetch inside global Advanced Search form without submitting search."""
        self.driver.get(cfg.EXPLORER_URL)
        self.wait_for_page_load()
        explorer_page.advanced_search(None, doc_type=doc_type, submit=False)
        WebDriverWait(self.driver, 10).until(
            lambda _d: bool(self.visible(f"#dms_search_form .meta-data-wrap input[name='{criteria_field}']"))
        )
        self.wait_for_ajax_idle(timeout=6)
        time.sleep(0.3)
        ok, msg = self._trigger_and_read_populated(
            "#dms_search_form .meta-data-wrap",
            criteria_field,
            criteria_value,
            populate_field,
            output_type,
            expected_value,
            expect_present=expect_present,
        )
        return ok, f"Advanced Search: {msg}"

    def verify_fetch_in_explorer_search(
        self,
        explorer_page,
        doc_type: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
    ) -> tuple[bool, str]:
        """Verify MTM fetch inside My Documents Explorer inline search panel."""
        explorer_page._navigate_tree_node(doc_type)
        if not self.visible("#meta_div"):
            btn = self.wait.until(EC.element_to_be_clickable((By.ID, "search_doc_explorer")))
            self.click(btn)
        self.wait.until(EC.visibility_of_element_located((By.ID, "meta_div")))
        WebDriverWait(self.driver, 10).until(
            lambda _d: bool(self.visible(f".meta-data-wrap-explorer input[name='{criteria_field}']"))
        )
        self.wait_for_ajax_idle(timeout=6)
        time.sleep(0.3)
        ok, msg = self._trigger_and_read_populated(
            ".meta-data-wrap-explorer",
            criteria_field,
            criteria_value,
            populate_field,
            output_type,
            expected_value,
            expect_present=expect_present,
            is_explorer=True,
        )
        return ok, f"Explorer Search: {msg}"

    def verify_fetch_all_contexts(
        self,
        session,
        doc_type: str,
        doc_name: str,
        criteria_field: str,
        criteria_value: str,
        populate_field: str,
        output_type: str,
        expected_value: str,
        expect_present: bool = True,
    ) -> tuple[bool, str]:
        """Run MTM fetch checks across Upload, Edit Metadata, Advanced Search, and Explorer Search."""
        results = [
            self.verify_fetch_in_upload(
                session.upload, doc_type, criteria_field, criteria_value,
                populate_field, output_type, expected_value, expect_present,
            ),
            self.verify_fetch_in_edit_metadata(
                session.explorer, doc_name, criteria_field, criteria_value,
                populate_field, output_type, expected_value, expect_present,
            ),
            self.verify_fetch_in_advanced_search(
                session.explorer, doc_type, criteria_field, criteria_value,
                populate_field, output_type, expected_value, expect_present,
            ),
            self.verify_fetch_in_explorer_search(
                session.explorer, doc_type, criteria_field, criteria_value,
                populate_field, output_type, expected_value, expect_present,
            ),
        ]
        all_ok = all(r[0] for r in results)
        summary = " | ".join(r[1] for r in results)
        return all_ok, summary
