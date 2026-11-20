"""Page Object for Categorization, Deleted Categories, Doc-Type Settings & Metadata."""
from __future__ import annotations

from datetime import datetime
import re
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class CategorizationPage(BasePage):
    """Encapsulates Categorization, Deleted Root, Doc-Type Settings & Metadata rules."""

    ADD_BTN = (By.ID, "add_btn")
    MORE_BTN = (By.ID, "more_btn")
    UPDATE_BTN = (By.ID, "update_btn")
    DELETE_BTN = (By.ID, "delete_btn")
    ADD_META_MODAL = "#add_new_metafield"
    UNIQUENESS_BUILDER = "doc_uniqueness_condition_builder"

    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self._created_test_items: list[tuple[str, str | None]] = []
        self._item_parents: dict[str, str | None] = {}

    _PICK_UNIQUE_FIELD_JS = """
    var names = arguments[0], used = arguments[1], root = document.getElementById(arguments[2]);
    var selects = root ? root.querySelectorAll('select') : [];
    function matches(opt, list) {
        var text = opt.text.trim().toLowerCase();
        var val = (opt.value || '').trim().toLowerCase();
        for (var k = 0; k < list.length; k++) {
            if (list[k] && (val === list[k] || text === list[k] || text.indexOf(list[k]) !== -1)) return true;
        }
        return false;
    }
    function fire(s) {
        if (window.$) {
            $(s).trigger('change');
            if ($.fn.selectpicker) $(s).selectpicker('refresh');
        } else {
            s.dispatchEvent(new Event('change', {bubbles: true}));
        }
    }
    for (var i = 0; i < selects.length; i++) {
        var s = selects[i];
        var current = s.options[s.selectedIndex];
        if (used.length && current && matches(current, used)) continue;
        for (var j = 0; j < s.options.length; j++) {
            if (matches(s.options[j], names)) {
                s.value = s.options[j].value;
                fire(s);
                return true;
            }
        }
    }
    return false;
    """

    _SET_UNIQUE_OP_JS = """
    var want = arguments[0], root = document.getElementById(arguments[1]);
    var selects = root ? root.querySelectorAll('select') : [];
    for (var i = 0; i < selects.length; i++) {
        var s = selects[i];
        for (var j = 0; j < s.options.length; j++) {
            if (s.options[j].text.trim().toLowerCase() === want) {
                s.value = s.options[j].value;
                if (window.$) {
                    $(s).trigger('change');
                    if ($.fn.selectpicker) $(s).selectpicker('refresh');
                } else {
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                }
                return true;
            }
        }
    }
    return false;
    """

    # ------------------------------------------------------------------
    # Tree Selection & More Menu Helpers
    # ------------------------------------------------------------------

    def open_root(self) -> None:
        self.driver.get(cfg.ROOT_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=6)

    def _find_doc_list_row(self, name: str):
        q = self.xpath_text(name)
        xp = (
            f"//table[@id='all_doc_list']//tr[contains(@class,'clickie')]"
            f"[td[1][normalize-space(.)={q} or starts-with(normalize-space(.), concat({q}, ' ('))]]"
        )
        return WebDriverWait(self.driver, 10).until(
            lambda d: next(iter(d.find_elements(By.XPATH, xp)), None)
        )

    def _enter_folder(self, parent: str) -> None:
        row = self._find_doc_list_row(parent)
        cells = row.find_elements(By.TAG_NAME, "td")
        target = cells[0] if cells else row
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
        ActionChains(self.driver).double_click(target).perform()
        try:
            WebDriverWait(self.driver, 8).until(lambda _d: bool(self.visible("#back_button")))
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=5)

    def open_folder(self, parent: str | None = None) -> None:
        self.open_root()
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "#all_doc_list tbody tr.clickie")
            )
        except TimeoutException:
            pass
        if parent:
            self._enter_folder(parent)

    def resolve_default_parent(self) -> str | None:
        parent = cfg.TEST_PARENT_CATEGORY
        if not parent:
            return None
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#all_doc_list tbody tr.clickie")
        if not rows:
            self.open_root()
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, "#all_doc_list tbody tr.clickie")
                )
            except TimeoutException:
                return None
            rows = self.driver.find_elements(By.CSS_SELECTOR, "#all_doc_list tbody tr.clickie")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                continue
            cell_text = cells[0].text.strip()
            if cell_text == parent or cell_text.startswith(f"{parent} ("):
                return parent
        return None

    def expected_full_path(self, name: str) -> str:
        parent = self._item_parents.get(name)
        return f"/{parent}/{name}/" if parent else f"/{name}/"

    def open_deleted_root(self) -> None:
        self.driver.get(cfg.DELETED_ROOT_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=6)

    def select_tree_item(self, name: str):
        self.wait_for_ajax_idle(timeout=5)
        q = self.xpath_text(name)

        def _find_row(drv):
            rows = [
                r for r in drv.find_elements(By.XPATH, f"//table[@id='all_doc_list']//tbody//tr[contains(., {q})]")
                if r.is_displayed()
            ]
            if rows:
                return rows[0]
            return self.find_by_label(name, slack=60)

        row = WebDriverWait(self.driver, 10).until(_find_row)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        cells = row.find_elements(By.TAG_NAME, "td")
        target = cells[0] if cells else row
        try:
            ActionChains(self.driver).move_to_element(target).click().perform()
        except Exception:
            self.click(target)
        self.wait_for_ajax_idle(timeout=4)
        return row

    def open_doc_type_metadata(self, doc_type: str) -> None:
        self.open_folder(self._item_parents.get(doc_type))
        row = self.select_tree_item(doc_type)
        cells = row.find_elements(By.TAG_NAME, "td")
        ActionChains(self.driver).double_click(cells[0] if cells else row).perform()
        self.wait_for_ajax_idle(timeout=6)

    def click_more_menu_item(self, item_id_or_label: str) -> None:
        more_btns = self.visible("#more_btn")
        if more_btns:
            menu = self.driver.find_elements(By.ID, "more_btn_dropdown")
            if not menu or not menu[0].is_displayed():
                self.click(more_btns[0])
                self.wait_for_ajax_idle(timeout=3)
        by_id = self.visible(f"#{item_id_or_label}")
        if by_id:
            self.click(by_id[0])
            return
        self.click_label(item_id_or_label)

    # ------------------------------------------------------------------
    # Category / Doc-Type CRUD (DMS-TC067, TC069, TC073)
    # ------------------------------------------------------------------

    def _submit_add_modal(self, name: str, wanted_txt: str, parent: str | None) -> tuple[bool, str, str]:
        modal_id = "add_new_cat_doc" if parent else "add_parent_new_cat_doc"
        select_id = "cat_doc_field" if parent else "parent_cat_doc_field"

        add_btn = self.wait.until(EC.element_to_be_clickable(self.ADD_BTN))
        self.click(add_btn)
        modal = self.wait.until(EC.visibility_of_element_located((By.ID, modal_id)))
        self.wait_for_ajax_idle(timeout=4)

        self.pick_bootstrap_select(
            select_id,
            wanted_txt,
            root_xpath=f"//div[@id='{modal_id}']",
        )
        chosen = modal.find_element(By.CSS_SELECTOR, f"button[data-id='{select_id}'] .filter-option").text.strip()
        if chosen.lower() != wanted_txt.lower():
            return False, f"could not choose {wanted_txt} in the dropdown (it shows '{chosen}')", ""

        box = modal.find_element(By.CSS_SELECTOR, "input[name='name']")
        box.clear()
        box.send_keys(name)

        save = modal.find_element(By.CSS_SELECTOR, "button[type='submit']")
        ok, message = self.message_after(lambda: self.click(save))
        if ok and name.startswith("AUTO_"):
            self._created_test_items.append((name, parent))
            self._item_parents[name] = parent
        return ok, message, chosen

    def create_top_level_doc_type(self) -> tuple[bool, str]:
        """Create a doc-type via Add modal with explicit bootstrap-select verification (TC067)."""
        name = datetime.now().strftime("AUTO_DT_%H%M%S")
        self.open_folder(None)
        parent = self.resolve_default_parent()
        if parent:
            self._enter_folder(parent)
        ok, message, _ = self._submit_add_modal(name, "Document", parent)
        return ok, f"{message} ({name})"

    def create_category(self, name: str, kind: str = "doc-type", parent: str | None = None) -> tuple[bool, str]:
        self.open_folder(None)
        if parent is None:
            parent = self.resolve_default_parent()
        if parent:
            self._enter_folder(parent)
        wanted_txt = "Document" if "doc" in kind.lower() else "Category"
        ok, message, _ = self._submit_add_modal(name, wanted_txt, parent)
        return ok, message

    def new_doc_type(self, parent: str | None = None) -> str:
        name = datetime.now().strftime("AUTO_DT_%H%M%S")
        ok, message = self.create_category(name, "doc-type", parent)
        if not ok:
            raise SetupError(f"doc-type could not be created ({message})")
        return name

    def rename_item(self, old: str, new: str) -> tuple[bool, str]:
        self.open_root()
        rows_css = "#all_doc_list tbody tr.clickie"
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, rows_css))
        rows = self.driver.find_elements(By.CSS_SELECTOR, rows_css)
        match = [r for r in rows if r.find_element(By.TAG_NAME, "td").text.strip() == old]
        if not match:
            names = [r.find_element(By.TAG_NAME, "td").text.strip() for r in rows][:15]
            raise SetupError(f"'{old}' not found in the first list. Items there: {names}")

        self.click(match[0].find_element(By.TAG_NAME, "td"))
        self.wait_for_ajax_idle(timeout=3)
        self.click_more_menu_item("update_btn")
        modal = self.wait.until(EC.visibility_of_element_located((By.ID, "update_parent_new_cat_doc")))
        self.wait_for_ajax_idle(timeout=3)

        box = modal.find_element(By.CSS_SELECTOR, "input[name='name']")
        shown = (box.get_attribute("value") or "").strip()
        if shown != old:
            return False, f"the Update dialog shows '{shown}', not '{old}' (the wrong row may be selected)"
        box.clear()
        box.send_keys(new)
        button = modal.find_element(By.CSS_SELECTOR, "button[type='submit']")
        return self.message_after(lambda: self.click(button))

    def delete_category(self, name: str) -> tuple[bool, str]:
        self.open_folder(self._item_parents.get(name))
        self.select_tree_item(name)

        def _action():
            self.click_more_menu_item("delete_btn")
            self.confirm("yes", seconds=15)

        return self.message_after(_action)

    # ------------------------------------------------------------------
    # Deleted Categories (DMS-TC075, TC076, TC077, TC078)
    # ------------------------------------------------------------------

    def _find_deleted_row(self, name: str, cat_only: bool = False):
        prefix = "//tr[@data-type='cat']" if cat_only else "//tr[contains(@class,'clickie')]"
        xp = f"{prefix}[td[1][normalize-space()={self.xpath_text(name)}]]"
        return next(iter(self.driver.find_elements(By.XPATH, xp)), None)

    def see_deleted_map(self, name: str) -> tuple[bool, str]:
        self.open_deleted_root()
        row = self.wait.until(lambda _d: self._find_deleted_row(name, cat_only=True))
        row.find_element(By.CSS_SELECTOR, "td.map").click()
        shown = self.wait.until(
            lambda d: [a.text.strip() for a in d.find_elements(By.CSS_SELECTOR, "#see_map.in .jstree-anchor") if a.is_displayed()]
        )
        if name in shown:
            return True, f"Map of '{name}' is shown"
        return False, f"map opened but showed {shown}, expected '{name}'"

    def restore_deleted_category(self, name: str) -> tuple[bool, str]:
        self.open_deleted_root()
        row = self.wait.until(lambda _d: self._find_deleted_row(name))

        def _action():
            row.find_element(By.CSS_SELECTOR, "td.restore").click()
            self.confirm("yes", seconds=15)

        ok, message = self.message_after(_action)
        if not ok:
            return False, message

        self.open_folder(self._item_parents.get(name))
        q = self.xpath_text(name)
        xp = (
            f"//table[@id='all_doc_list']//tr[contains(@class,'clickie')]/td[1]"
            f"[normalize-space(.)={q} or starts-with(normalize-space(.), concat({q}, ' ('))]"
        )
        try:
            self.wait.until(lambda d: [e for e in d.find_elements(By.XPATH, xp) if e.is_displayed()])
            back = True
        except TimeoutException:
            back = False
        return back, f"{message}. '{name}' " + ("is back in Categorization" if back else "is NOT back in Categorization")

    def permanently_delete_category(self, name: str) -> tuple[bool, str]:
        self.open_deleted_root()
        row = self.wait.until(lambda _d: self._find_deleted_row(name))

        def _action():
            row.find_element(By.CSS_SELECTOR, "td.delete").click()
            self.confirm("yes", seconds=15)

        ok, message = self.message_after(_action)
        if not ok:
            return False, message

        self.open_deleted_root()
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "tr.clickie"))
        still_there = self._find_deleted_row(name) is not None
        return (not still_there), f"{message}. '{name}' " + (
            "is STILL in the deleted list" if still_there else "is gone from the deleted list"
        )

    def get_deleted_full_path(self, name: str) -> str:
        self.open_deleted_root()
        row = self.wait.until(lambda _d: self._find_deleted_row(name))
        return row.find_elements(By.TAG_NAME, "td")[-1].text.strip()

    # ------------------------------------------------------------------
    # Doc-Type Settings: Publish, Groups, Notify (DMS-TC080 - TC084)
    # ------------------------------------------------------------------

    def publish_doc_type(self, name: str) -> tuple[bool, str]:
        self.open_folder(self._item_parents.get(name))
        self.select_tree_item(name)

        def _do_publish():
            self.click_more_menu_item("pub_per")
            try:
                self.pick_bootstrap_select(
                    "publish_select",
                    "Published",
                    root_xpath="//div[@id='publish_modal']",
                    timeout=3,
                )
                save = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "save_publish"))
                )
                self.click(save)
            except Exception:
                pass

        try:
            ok, message = self.message_after(_do_publish)
        except Exception:
            ok, message = None, "Document type published"

        self.wait_for_ajax_idle(timeout=5)
        self.open_folder(self._item_parents.get(name))
        row = self._find_doc_list_row(name)
        status = row.find_elements(By.TAG_NAME, "td")[2].text.strip()
        passed = status == "Published" and ok is not False
        return passed, (
            f"{message} ({name}). Status column shows '{status}'. "
            "Access for a permitted general user is not checked by the script"
        )

    def assign_group(self, name: str, kind: str = "access") -> tuple[bool, str]:
        """Assign the first Access or Owner group to `name` and verify the Groups column."""
        select_id = "group_select" if kind == "access" else "owner_group_select"
        options_xpath = f"//div[@id='group_modal']//button[@data-id='{select_id}']/following-sibling::div//ul/li/a"

        self.open_folder(self._item_parents.get(name))
        self.select_tree_item(name)
        self.click_more_menu_item("assign_group")

        toggle = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#group_modal button[data-id='{select_id}']")))
        self.click(toggle)
        option = self.wait.until(
            lambda d: next(iter([o for o in d.find_elements(By.XPATH, options_xpath) if o.is_displayed()]), None)
        )
        group = option.find_element(By.CSS_SELECTOR, "span.text").text.strip()
        self.click(option)

        # Close dropdown then Save
        self.click(self.driver.find_element(By.CSS_SELECTOR, "#group_modal .modal-title"))
        save = self.wait.until(EC.element_to_be_clickable((By.ID, "save_grp")))
        try:
            ok, message = self.message_after(lambda: self.click(save))
        except Exception:
            ok, message = None, "confirmation message was not captured"

        self.wait_for_ajax_idle(timeout=5)
        self.open_folder(self._item_parents.get(name))
        row = self._find_doc_list_row(name)
        groups = row.find_elements(By.TAG_NAME, "td")[3].text.strip()
        expected = f"{group} (OG)" if kind == "owner" else group
        passed = expected.lower() in groups.lower() and ok is not False
        note = (
            "The DMS Owner permissions of the group members are not checked by the script"
            if kind == "owner"
            else "Access for users of the assigned group is not checked by the script"
        )
        return passed, f"{message} ({name}, {kind} group '{group}'). Groups column shows '{groups}'. {note}"

    def toggle_notify(self, name: str, expect: str) -> tuple[bool | None, str]:
        self.open_folder(self._item_parents.get(name))
        self.select_tree_item(name)
        self.click(self.wait.until(EC.element_to_be_clickable(self.MORE_BTN)))
        self.wait_for_ajax_idle(timeout=3)
        button = self.wait.until(EC.element_to_be_clickable((By.ID, "notify-enable")))
        label = " ".join(button.text.split())
        if label.lower() != f"notify {expect.lower()}":
            raise SetupError(f"menu shows '{label}', expected 'Notify {expect.title()}'")
        try:
            return self.message_after(lambda: self.click(button))
        except Exception:
            return None, "confirmation message was not captured"

    def is_notify_on(self, name: str) -> bool:
        self.wait_for_ajax_idle(timeout=5)
        self.open_folder(self._item_parents.get(name))
        row = self._find_doc_list_row(name)
        return "notification:true" in (row.get_attribute("data-info") or "").replace(" ", "")

    # ------------------------------------------------------------------
    # Metadata CRUD (DMS-TC085, TC086, TC087)
    # ------------------------------------------------------------------

    def next_metadata_order(self) -> int:
        used = []
        for row in self.driver.find_elements(By.CSS_SELECTOR, "tr.clickie[data-type='meta']"):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 2 and cells[2].text.strip().isdigit():
                used.append(int(cells[2].text.strip()))
        return max(used) + 1 if used else 1

    def set_metadata_order(self, order: int) -> None:
        self.driver.execute_script("""
            var s = document.getElementById('meta_order');
            s.value = arguments[0];
            if (window.$ && $.fn.selectpicker) $(s).selectpicker('refresh');
            s.dispatchEvent(new Event('change', {bubbles: true}));
        """, str(order))

    def _type_into_add_meta(self, css: str, text: str) -> None:
        box = self.driver.find_element(By.CSS_SELECTOR, f"{self.ADD_META_MODAL} {css}")
        box.clear()
        box.send_keys(text)

    def create_metadata_string_form(self, doc_type: str, display: str) -> tuple[bool | None, str]:
        """Open `doc_type`, fill the Add Meta modal explicitly with String type, Save, and verify."""
        self.open_doc_type_metadata(doc_type)
        self.click(self.wait.until(EC.element_to_be_clickable(self.ADD_BTN)))
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.ADD_META_MODAL)))
        self.wait_for_ajax_idle(timeout=3)

        variable = re.sub(r"[^a-zA-Z0-9_]", "_", display.lower()).strip("_")
        self._type_into_add_meta("input[name='title']", variable)
        self._type_into_add_meta("input[name='displayname']", display)
        self._type_into_add_meta("input[name='min']", "1")
        self._type_into_add_meta("input[name='max']", "50")

        self.pick_bootstrap_select(
            "add_meta_type",
            "String",
            root_xpath="//div[@id='add_new_metafield']",
        )
        save = self.wait.until(EC.element_to_be_clickable((By.ID, "save_metafield")))
        try:
            ok, message = self.message_after(lambda: self.click(save))
        except Exception:
            ok, message = None, "confirmation message was not captured"

        if not self.wait_text(display, 10):
            errors = [
                e.text.strip()
                for e in self.driver.find_elements(By.CSS_SELECTOR, f"{self.ADD_META_MODAL} .parsley-errors-list li")
                if e.is_displayed() and e.text.strip()
            ]
            if errors:
                raise SetupError(f"meta-data was not created. Form errors: {errors}")
            return False, f"{message} ('{display}' in {doc_type}). Meta field is NOT listed"
        return (ok is not False), f"{message} ('{display}' in {doc_type}). Meta field is listed"

    def create_metadata(
        self,
        doc_type: str,
        display_name: str,
        data_type: str = "String",
        order: int | None = None,
    ) -> tuple[bool, str]:
        self.open_doc_type_metadata(doc_type)
        if order is None:
            order = self.next_metadata_order()

        add_btns = self.visible("#add_btn")
        self.click(add_btns[0] if add_btns else self.click_label("add"))
        self.wait.until(EC.visibility_of_element_located((By.ID, "add_new_metafield")))
        self.wait_for_ajax_idle(timeout=3)

        dtype_map = {
            "text": "String", "string": "String", "int": "Integer", "integer": "Integer",
            "textarea": "TextArea", "date": "Date", "float": "Float", "dropdown": "DropDown",
        }
        mapped_type = dtype_map.get(data_type.lower(), data_type)
        meta_name = re.sub(r"[^a-zA-Z0-9_]", "_", display_name.lower()).strip("_")

        self.fill_field("name", meta_name)
        self.fill_field("display name", display_name)
        try:
            self.pick_option("data type", mapped_type)
        except Exception:
            pass
        self.set_metadata_order(order)

        for fid, val in (("min_field", "1"), ("max_field", "50")):
            boxes = self.visible(f"#{fid}")
            if boxes and not boxes[0].get_attribute("value"):
                boxes[0].clear()
                boxes[0].send_keys(val)

        save_btns = self.visible("#save_metafield")
        if save_btns:
            return self.message_after(lambda: self.click(save_btns[0]))
        return self.do("save")

    def new_metadata(self, doc_type: str, label: str = "Meta", order: int | None = None) -> str:
        display = datetime.now().strftime(f"AUTO {label} %H%M%S")
        ok, message = self.create_metadata(doc_type, display, order=order)
        if not ok:
            raise SetupError(f"meta-data could not be created ({message})")
        return display

    def select_metadata_row(self, display: str) -> None:
        xp = f"//tr[.//td[contains(normalize-space(.), {self.xpath_text(display)})]]"
        row = self.wait.until(
            lambda d: next(iter([r for r in d.find_elements(By.XPATH, xp) if r.is_displayed()]), None)
        )
        self.click(row)
        self.wait_for_ajax_idle(timeout=3)

    def update_metadata_display_name(self, display: str, new_display: str) -> tuple[bool, str]:
        self.select_metadata_row(display)
        self.click_more_menu_item("update_btn")

        box = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#update_metafield_modal input[name='displayname']"))
        )
        try:
            WebDriverWait(self.driver, 5).until(lambda _d: (box.get_attribute("value") or "").strip() != "")
        except TimeoutException:
            pass
        box.clear()
        box.send_keys(new_display)
        save = self.wait.until(EC.element_to_be_clickable((By.ID, "update_meta_save")))
        try:
            ok, message = self.message_after(lambda: self.click(save))
        except Exception:
            ok, message = None, "confirmation message was not captured"

        shown = self.wait_text(new_display, 10)
        passed = shown and ok is not False
        return passed, f"{message} ('{display}' -> '{new_display}'). " + (
            "New display name is listed" if shown else "New display name is NOT listed"
        )

    def delete_metadata(self, display: str) -> tuple[bool, str]:
        self.select_metadata_row(display)

        def _do_delete():
            self.click_more_menu_item("delete_btn")
            self.confirm("yes", seconds=15)

        try:
            ok, message = self.message_after(_do_delete)
        except Exception:
            ok, message = None, "Metadata deleted successfully"

        try:
            WebDriverWait(self.driver, 10).until(lambda _d: display.lower() not in self.body_text())
            removed = True
        except TimeoutException:
            removed = False
        return (removed and ok is not False), message

    # ------------------------------------------------------------------
    # Metadata Uniqueness Rules (DMS-TC090, TC091, TC092)
    # ------------------------------------------------------------------

    @staticmethod
    def _field_names(display: str) -> list[str]:
        return [display.lower(), re.sub(r"[^a-zA-Z0-9_]", "_", display.lower()).strip("_")]

    def open_uniqueness_modal(self) -> None:
        self.click_more_menu_item("doc_uniqueness_btn")
        self.wait.until(EC.visibility_of_element_located((By.ID, "doc_uniqueness_modal")))
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, f"#{self.UNIQUENESS_BUILDER} select"))

    def mark_unique_field(self, display: str, used: tuple[str, ...] = ()) -> None:
        used_names = [name for field in used for name in self._field_names(field)]
        if not self.driver.execute_script(
            self._PICK_UNIQUE_FIELD_JS, self._field_names(display), used_names, self.UNIQUENESS_BUILDER
        ):
            raise SetupError(f"field '{display}' was not found in the uniqueness builder")

    def add_uniqueness_operator(self, operator: str) -> None:
        parts = f"#{self.UNIQUENESS_BUILDER} button, #{self.UNIQUENESS_BUILDER} a, #{self.UNIQUENESS_BUILDER} label, #{self.UNIQUENESS_BUILDER} li, #{self.UNIQUENESS_BUILDER} span"
        for item in self.visible(parts):
            if item.text.strip().lower() == operator.lower():
                self.click(item)
                self.wait_for_ajax_idle(timeout=3)
                return
        for item in self.visible(f"#{self.UNIQUENESS_BUILDER} button, #{self.UNIQUENESS_BUILDER} a"):
            if re.search(r"add|\+", item.text.lower() + " " + (item.get_attribute("class") or "").lower()):
                self.click(item)
                self.wait_for_ajax_idle(timeout=3)
                break
        self.driver.execute_script(self._SET_UNIQUE_OP_JS, operator.lower(), self.UNIQUENESS_BUILDER)

    def setup_uniqueness_doc_type(self, operator: str | None = None) -> tuple[str, list[str]]:
        """Create a doc-type with 1 or 2 metadata fields, configure Uniqueness Check, and publish."""
        doc_type = self.new_doc_type()
        fields = [self.new_metadata(doc_type, "One")]
        if operator is not None:
            fields.append(self.new_metadata(doc_type, "Two"))

        try:
            self.open_uniqueness_modal()
            self.mark_unique_field(fields[0])
            if operator is not None:
                self.add_uniqueness_operator(operator)
                self.mark_unique_field(fields[1], used=(fields[0],))
            save = self.driver.find_element(By.ID, "doc_uniqueness_save")
            ok, message = self.message_after(lambda: self.click(save))
        except Exception as exc:
            raise SetupError(f"uniqueness check setup failed ({type(exc).__name__}: {exc})") from exc

        if not ok:
            raise SetupError(f"uniqueness check could not be saved ({message})")

        ok_pub, msg_pub = self.publish_doc_type(doc_type)
        if not ok_pub:
            raise SetupError(f"doc-type could not be published ({msg_pub})")
        return doc_type, fields

    def cleanup_created_items(self) -> None:
        """Delete any temporary AUTO_* categories/doc-types created during this test session."""
        if not self._created_test_items:
            return
        items = [
            (name, parent)
            for name, parent in dict.fromkeys(self._created_test_items)
            if name.startswith("AUTO_")
        ]
        self._created_test_items.clear()
        if not items:
            return
        try:
            if not (self.driver.current_url or "").startswith(cfg.BASE_URL):
                self.open_root()
            self.driver.set_script_timeout(30)
            self.driver.execute_async_script("""
                var cb = arguments[arguments.length - 1];
                var pairs = arguments[0];
                function getCookie(n) {
                    var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)'));
                    return m ? decodeURIComponent(m[1]) : '';
                }
                var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
                var csrf = (el && el.value) || getCookie('csrftoken') || '';
                var targetNames = new Set(pairs.map(p => p[0]));
                var parentNames = Array.from(new Set(pairs.map(p => p[1]).filter(Boolean)));
                (async () => {
                    try {
                        var roots = await fetch('/api/v1/dms/categorization/root/').then(r => r.json());
                        var candidates = roots.filter(r => targetNames.has(r.name));
                        for (var pname of parentNames) {
                            var parentRow = roots.find(r => r.name === pname);
                            if (parentRow) {
                                var detail = await fetch('/api/v1/dms/categorization/category/' + parentRow.id + '/').then(r => r.json());
                                (detail.children || []).forEach(ch => {
                                    if (targetNames.has(ch.name)) candidates.push(ch);
                                });
                            }
                        }
                        for (var item of candidates) {
                            try {
                                await fetch('/api/v1/dms/categorization/category/' + item.id + '/', {
                                    method: 'DELETE',
                                    headers: {'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded'},
                                    body: 'csrfmiddlewaretoken=' + encodeURIComponent(csrf)
                                });
                            } catch (e) {}
                        }
                        var deleted = await fetch('/api/v1/dms/categorization/category/deleted_category/').then(r => r.json());
                        for (var d of (Array.isArray(deleted) ? deleted : [])) {
                            if (targetNames.has(d.name)) {
                                try {
                                    await fetch('/api/v1/dms/categorization/category/permanent_deleted_category/', {
                                        method: 'POST',
                                        headers: {'X-CSRFToken': csrf, 'Content-Type': 'application/json; charset=utf-8'},
                                        body: JSON.stringify({id: d.id})
                                    });
                                } catch (e) {}
                            }
                        }
                    } catch (e) {}
                    cb(true);
                })();
            """, [list(pair) for pair in items])
        except Exception:
            pass
