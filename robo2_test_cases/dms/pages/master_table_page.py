"""Page Object for DMS Master Table Method (Fetch) settings."""
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
    """Encapsulates Master Table Method creation, editing, cloning, filtering & assignment."""

    MTM_FORM = "#mtm_creation_main_form"

    _PICK_OPTION_JS = """
    var s = document.querySelector(arguments[0]);
    if (!s) return '';
    var want = (arguments[1] || '').toLowerCase();
    var chosen = null;
    for (var i = 0; i < s.options.length; i++) {
        var o = s.options[i];
        if (o.disabled || !o.value) continue;
        if (!want || o.text.trim().toLowerCase() === want || o.value.toLowerCase() === want) { chosen = o; break; }
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

    def open(self) -> None:
        self.driver.get(cfg.MASTER_TABLE_URL)
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            lambda _d: bool(self.visible(".mtm-list-card, .MTM-empty-card"))
        )
        self.wait_for_ajax_idle(timeout=4)

    def _card_xpath(self, name: str) -> str:
        return (
            f"//div[contains(concat(' ', normalize-space(@class), ' '), ' mtm-list-card ')"
            f" and .//span[@title={self.xpath_text(name)}]]"
        )

    def _open_card_action(self, name: str, button_css: str):
        """Find a method card by title, expand its settings gear if needed, and return (card_xpath, button)."""
        card_xpath = self._card_xpath(name)
        try:
            card = WebDriverWait(self.driver, 10).until(
                lambda d: next(iter(d.find_elements(By.XPATH, card_xpath)), None)
            )
            button = card.find_element(By.CSS_SELECTOR, button_css)
            if not button.is_displayed():
                self.click(card.find_element(By.CSS_SELECTOR, "a.mtm_setting_button"))
                WebDriverWait(self.driver, 5).until(lambda _d: button.is_displayed())
            return card_xpath, button
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' was not found in the method list") from exc

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

    def mtm_pick_master_table(self) -> str:
        wanted = os.getenv("MTM_MASTER_TABLE")
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

    def create_method(self, record_type: str = "multiple record") -> tuple[bool, str, str]:
        self.driver.get(cfg.MASTER_TABLE_URL)
        self.wait_for_ajax_idle(timeout=6)
        add_buttons = self.visible("#dms_method_add")
        if add_buttons:
            self.click(add_buttons[0])
        else:
            self.click_label("add method")
        self.wait.until(EC.visibility_of_element_located((By.ID, "mtm_creation_main_form")))
        self.wait_for_ajax_idle(timeout=4)

        name = datetime.now().strftime("AUTO_MT_%H%M%S")
        self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]').send_keys(name)
        try:
            self.mtm_pick_master_table()
            self.mtm_pick_doc_type(os.getenv("MTM_DOC_TYPE", "aa"))
            self.mtm_choose("mtm_output_type", "multiple" if "multiple" in record_type.lower() else "single")
            self.wait_for_ajax_idle(timeout=4)
            for field in ("mtm_fetch_all_record", "mtm_unique_fetch_record"):
                if self.mtm_field_visible(field):
                    self.mtm_choose(field, "false")
            self.mtm_choose("mtm_match_criteria_mt_field")
            self.mtm_choose("mtm_match_criteria_operator")
            self.mtm_choose("mtm_match_criteria_value_type", "meta_data_field")
            self.mtm_choose("mtm_match_criteria_metadata_field")
            self.mtm_choose("mtm_populate_mt_field")
            self.mtm_choose("mtm_populate_metadata_field")
            save = self.driver.find_element(By.ID, "save_mtm_dms")
            ok, message = self.message_after(lambda: self.click(save))
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' was not saved. The form says: {self.form_problems() or 'nothing'}") from exc
        return ok, message, name

    def new_method(self, record_type: str = "multiple record") -> str:
        ok, message, name = self.create_method(record_type)
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

    def update_method(self, name: str, new_name: str) -> tuple[bool, str]:
        card_xpath = self._card_xpath(name)
        try:
            card = WebDriverWait(self.driver, 10).until(
                lambda d: next(iter(d.find_elements(By.XPATH, card_xpath)), None)
            )
            self.click(card.find_element(By.CSS_SELECTOR, "a.mtm_edit_button"))
            self._wait_form_populated(expected_name=name)
        except TimeoutException as exc:
            raise SetupError(f"the edit form of method '{name}' did not open or fill in") from exc

        title = self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]')
        title.clear()
        title.send_keys(new_name)
        try:
            save = self.driver.find_element(By.ID, "save_mtm_dms")
            ok, message = self.message_after(lambda: self.click(save))
        except TimeoutException as exc:
            raise SetupError(f"method '{name}' was not updated. The form says: {self.form_problems() or 'nothing'}") from exc
        listed = self.wait_text(new_name, 8)
        return ok and listed, message + ("" if listed else f". '{new_name}' is not in the method list")

    def delete_method(self, name: str) -> tuple[bool, str]:
        card_xpath, button = self._open_card_action(name, "button.mtm_delete_button")

        def _action():
            self.click(button)
            self.confirm("yes", seconds=15)

        ok, message = self.message_after(_action)
        try:
            WebDriverWait(self.driver, 8).until(lambda d: not d.find_elements(By.XPATH, card_xpath))
            gone = True
        except TimeoutException:
            gone = False
        return ok and gone, message + (". Method removed from the list" if gone else ". Method still shown in the list")

    def set_method_disabled(self, name: str, target_disabled: bool) -> tuple[bool, str]:
        """Toggle Disable/Enable on a method card and verify `data-mtm-disabled`."""
        card_xpath, button = self._open_card_action(name, "button.mtm_disable_button")

        def _action():
            self.click(button)
            try:
                self.confirm("yes", seconds=5)
            except Exception:
                pass

        ok, message = self.message_after(_action)
        expected_attr = "true" if target_disabled else "false"
        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: d.find_element(By.XPATH, card_xpath).get_attribute("data-mtm-disabled") == expected_attr
            )
            state_ok = True
        except TimeoutException:
            state_ok = False
        return (ok or state_ok), message

    def clone_method(self, name: str) -> tuple[bool, str]:
        _card_xpath, button = self._open_card_action(name, "button.mtm_clone_button")
        clone_name = f"{name}_CLONE"

        def _action():
            self.click(button)
            self.wait_for_ajax_idle(timeout=4)
            form = self.driver.find_elements(By.ID, "mtm_creation_main_form")
            if form and form[0].is_displayed():
                self._wait_form_populated()
                title = self.driver.find_element(By.CSS_SELECTOR, f'{self.MTM_FORM} input[name="method_name"]')
                current_title = (title.get_attribute("value") or "").strip()
                if not current_title or current_title == name:
                    title.clear()
                    title.send_keys(clone_name)
                self.click(self.driver.find_element(By.ID, "save_mtm_dms"))
                return
            try:
                self.confirm("yes", seconds=5)
            except Exception:
                pass

        return self.message_after(_action)

    def filter_by_doc_type(self, doc_type: str) -> tuple[bool, str]:
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
        for card in cards:
            spans = card.find_elements(By.CSS_SELECTOR, ".summary-item i[title='Document Type'] + span")
            doc_types_shown.append(spans[0].text.strip() if spans else card.text.strip())

        target = chosen.strip().strip("/").split("/")[-1].lower()
        wrong = [dt for dt in doc_types_shown if target not in dt.lower()]
        ok = bool(cards) and not wrong
        return ok, (
            f"Filter '{chosen}' shows {len(cards)} methods"
            + ("" if ok else f", {len(wrong)} of them do not belong to this doc-type")
        )

    def search_method(self, name: str) -> tuple[bool, str]:
        self.open()
        search_box = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input.method_search_input"))
        )
        search_box.click()
        search_box.clear()
        search_box.send_keys(name, Keys.ENTER)
        self.wait_for_ajax_idle(timeout=6)

        cards = self.visible(".method-list-card-container .mtm-list-card")
        shown_names = []
        for card in cards:
            spans = card.find_elements(By.CSS_SELECTOR, ".summary-item i[title='Method'] + span")
            shown_names.append(spans[0].text.strip() if spans else card.text.strip())

        wrong = [m for m in shown_names if name.lower() not in m.lower()]
        ok = bool(cards) and not wrong
        return ok, f"Search '{name}' shows {len(cards)} method(s)" + ("" if ok else f", {len(wrong)} do not match")

    def assign_method(self, name: str, doc_type: str) -> tuple[bool, str]:
        _card_xpath, button = self._open_card_action(name, "button.mtm_assign_button")
        assign_box = "#method_assign_to_document_type_parent"

        def _action():
            self.click(button)
            self.wait.until(EC.visibility_of_element_located((By.ID, "on_assign_method_doc_type_modal")))
            self.wait_for_ajax_idle(timeout=4)
            self._type_and_pick_select2(
                assign_box,
                f"{assign_box} input.select2-search__field",
                ".select2-container--open .select2-results__option",
                (doc_type or "aa").strip(),
            )
            if not self.driver.find_elements(By.CSS_SELECTOR, f"{assign_box} li.select2-selection__choice"):
                raise SetupError(f"document type '{doc_type}' could not be selected in the Assign To box")
            self.click(self.driver.find_element(By.ID, "on_assign_method_doc_type_modal_form_save_btn"))

        try:
            ok, message = self.message_after(_action)
        except TimeoutException as exc:
            problem = self.driver.find_element(By.ID, "doc_type_assign_error_div").text.strip()
            raise SetupError(f"method '{name}' was not assigned. The window says: {problem or 'nothing'}") from exc

        problem = self.driver.find_element(By.ID, "doc_type_assign_error_div").text.strip()
        return ok, (
            f"{message} ({name} -> {doc_type})"
            + (f". Window says: {problem}" if problem else "")
            + ". Fetched data on the upload page is not checked by the script"
        )
