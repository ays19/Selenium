"""Page Object for the Document Full View / Details screen."""
from __future__ import annotations

import os
import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage


class DocumentViewPage(BasePage):
    """Encapsulates interactions on an opened Document View page."""

    VERSION_HISTORY_PANEL = (By.ID, "versionHistory")
    ADD_VERSION_MODAL = (By.ID, "addVersion")
    EDIT_METADATA_INPUTS = "input[type='text'], input[type='number'], textarea"
    RELATED_BTN = (By.CSS_SELECTOR, "button[data-type='related']")
    ADD_RELATED_MODAL = (By.ID, "addRelated")
    SHARE_PANEL = (By.ID, "share_document")
    EMAIL_SHARE_BTN = (By.ID, "email_share_document")
    EMAIL_SHARE_MODAL = (By.ID, "email_share_document_modal")
    SYSTEM_META_BODY = (By.ID, "systemDefinedMetaDataBody")
    OCR_STATUS = (By.ID, "ocr-status")
    AI_CHAT_INPUT = (By.ID, "ai-chat")
    AI_CHAT_SUBMIT = (By.ID, "ai-chat-submit")
    AI_CHAT_HISTORY = (By.ID, "scroll-bar")

    SHARE_DELETE_SELECTORS = (
        "#share_document #delete_share_document, "
        "#share_document button[data-type*='delete' i], "
        "#share_document button[data-type*='unshare' i], "
        "#share_document button[title*='Delete' i], "
        "#share_document a[title*='Delete' i]"
    )

    
    # Metadata Editing (DMS-TC019)
    

    def _open_edit_metadata_modal(self) -> None:
        if self.find_by_label("edit metadata") is not None:
            self.click_label("edit metadata")
        else:
            edit_btns = self.driver.find_elements(
                By.XPATH,
                "//*[normalize-space(text())='Meta Data']/ancestor::*[position()<=3]//*[self::button or self::a or self::i] | "
                "//*[contains(@title, 'Edit') or contains(@data-original-title, 'Edit') or contains(@class, 'edit')]",
            )
            for btn in edit_btns:
                if btn.is_displayed():
                    self.click(btn)
                    break

        self.wait.until(EC.visibility_of_element_located((By.ID, "editMeta")))
        try:
            WebDriverWait(self.driver, 15).until(
                lambda _d: bool(self.visible("#editMeta .meta-data-gen-wrap input, #editMeta .meta-data-gen-wrap textarea"))
                and not self.visible("#updateMetadataForm #loaderOverlay")
            )
        except TimeoutException:
            pass
        self.wait_for_ajax_idle(timeout=6)

    def edit_metadata_field_and_save(self) -> tuple[bool, str]:
        self._open_edit_metadata_modal()

        scoped = "#editMeta .meta-data-gen-wrap input[type='text'], #editMeta .meta-data-gen-wrap input[type='number'], #editMeta .meta-data-gen-wrap textarea"
        fields = [
            f for f in self.visible(scoped)
            if f.is_enabled()
            and not f.get_attribute("readonly")
            and "date" not in (f.get_attribute("id") or "").lower()
        ]
        ours = [f for f in fields if (f.get_attribute("value") or "").startswith("AUTO_")]
        if not (ours or fields):
            return False, "no editable meta-data field found in #editMeta"

        target = (ours or fields)[0]
        outer = (target.get_attribute("outerHTML") or "").lower()
        old_val = target.get_attribute("value") or ""
        suffix = "9" if any(w in outer for w in ("digits", "number", "integer", "numeric")) else "_EDIT"
        new_val = old_val + suffix
        target.send_keys(suffix)

        old_html = self.driver.find_element(By.TAG_NAME, "html")
        save_btn = self.find_by_label("save changes") or self.find_by_label("save")
        if save_btn is None:
            return False, "Save Changes button not found in #editMeta"
        ok, msg = self.message_after(lambda: self.click(save_btn))
        if not ok:
            return False, msg

        try:
            WebDriverWait(self.driver, 10).until(EC.staleness_of(old_html))
        except TimeoutException:
            self.driver.refresh()
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=6)

        persisted = WebDriverWait(self.driver, 10).until(
            lambda d: new_val in (d.find_element(By.ID, "metaData").text or "")
        )
        if not persisted:
            return False, f"{msg}, but updated metadata '{new_val}' did not persist after reload"
        return True, f"{msg} (updated value '{new_val}' persisted)"

    def edit_metadata_values(self, values: dict[str, str]) -> tuple[bool, str]:
        """Set explicit field values in #editMeta and click Save Changes without reloading."""
        self._open_edit_metadata_modal()
        for label, value in values.items():
            self.fill_field(label, value)
        save_btn = self.find_by_label("save changes") or self.find_by_label("save")
        if save_btn is None:
            return False, "Save Changes button not found in #editMeta"
        return self.message_after(lambda: self.click(save_btn))

    
    # Version History (DMS-TC014, TC015, TC016)
    

    def add_version(self, pdf_copy_path: str, suffix: str = "v2") -> tuple[bool, str]:
        add_btns = self.driver.find_elements(
            By.CSS_SELECTOR, "#version-history-id button[data-type='version'], button[data-type='version']"
        )
        if add_btns:
            self.click(add_btns[0])
        else:
            self.click_label("version history")
            self.click_label("add")

        self.wait.until(EC.visibility_of_element_located(self.ADD_VERSION_MODAL))
        self.wait_for_ajax_idle(timeout=5)
        self.attach_to_file_input(pdf_copy_path)
        self.wait_for_ajax_idle(timeout=5)

        extra = self.driver.find_elements(By.ID, "file_name_extended_part")
        box = extra[0] if extra and extra[0].is_displayed() else self.modal_text_input()
        if box is not None:
            box.clear()
            box.send_keys(suffix)

        self.driver.execute_script("""
            var sel = document.getElementById('version');
            if (sel && !sel.value) {
                for (var i = 0; i < sel.options.length; i++) {
                    if (sel.options[i].value) { sel.value = sel.options[i].value; break; }
                }
                if (window.$ && $.fn.selectpicker) $(sel).selectpicker('refresh');
            }
            var cmt = document.getElementById('vcomment');
            if (cmt && !cmt.value.trim()) cmt.value = 'Version upload';
        """)

        old_html = self.driver.find_element(By.TAG_NAME, "html")
        upload_btns = self.driver.find_elements(By.CSS_SELECTOR, "#addVersion button[data-type='uploadVersion']")
        if upload_btns:
            ok, msg = self.message_after(lambda: self.click(upload_btns[0]))
        else:
            ok, msg = self.do("upload")
        if ok:
            try:
                WebDriverWait(self.driver, 6).until(EC.staleness_of(old_html))
            except TimeoutException:
                pass
            self.wait_for_page_load()
            self.wait_for_ajax_idle(timeout=5)
        return ok, msg

    def show_versions(self, version_text: str) -> None:
        panels = self.driver.find_elements(*self.VERSION_HISTORY_PANEL)
        if panels:
            cls = (panels[0].get_attribute("class") or "").split()
            if not panels[0].is_displayed() or "in" not in cls:
                headers = self.driver.find_elements(By.CSS_SELECTOR, "#version-history-id .card-header")
                if headers:
                    self.click(headers[0])
                else:
                    self.click_label("version history")
            try:
                WebDriverWait(self.driver, 6).until(
                    lambda d: any(
                        p.is_displayed() and version_text.lower() in (p.text or "").lower()
                        for p in d.find_elements(*self.VERSION_HISTORY_PANEL)
                    )
                )
            except TimeoutException:
                pass
        elif self.find_by_label(version_text, slack=300) is None:
            self.click_label("version history")
            self.wait_for_ajax_idle(timeout=5)

    def _find_version_action(self, version_text: str, action: str):
        xp = (
            f"//div[@id='versionHistory']//div[contains(@class, 'media-body')]"
            f"[contains(., {self.xpath_text(version_text)})]//a[@data-action={self.xpath_text(action)}]"
        )
        for btn in self.driver.find_elements(By.XPATH, xp):
            if btn.is_displayed():
                return btn
        panels = [p for p in self.driver.find_elements(*self.VERSION_HISTORY_PANEL) if p.is_displayed()]
        if panels:
            return self.find_near(version_text, action, root=panels[0])
        return None

    def is_version_listed(self, version_text: str, timeout: int = 8) -> bool:
        self.show_versions(version_text)
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: any(
                    p.is_displayed() and version_text.lower() in (p.text or "").lower()
                    for p in d.find_elements(*self.VERSION_HISTORY_PANEL)
                )
            )
            return True
        except TimeoutException:
            return False

    def download_version(self, version_text: str) -> str | None:
        self.show_versions(version_text)
        btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_version_action(version_text, "download"))
        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        started = time.time()
        self.click(btn)
        return self.wait_for_download(before, started=started)

    def delete_version(self, version_text: str) -> tuple[bool, str]:
        self.show_versions(version_text)
        btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_version_action(version_text, "delete"))
        old_html = self.driver.find_element(By.TAG_NAME, "html")

        def _action():
            self.click(btn)
            if not self.confirm("yes"):
                raise AssertionError("Confirmation dialog ('Yes, delete!') did not appear for version delete")

        ok, message = self.message_after(_action)
        if not ok:
            return False, message
        try:
            WebDriverWait(self.driver, 8).until(EC.staleness_of(old_html))
        except TimeoutException:
            self.driver.refresh()
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=5)
        if self.is_version_listed(version_text, timeout=4):
            return False, f"{message}, but version '{version_text}' is still listed in #versionHistory"
        return True, f"{message}. Version '{version_text}' removed from version history"

    
    # Lifecycle: Checkout, Download, Full View, Archive, Delete
    

    def _wait_reload_after_action(self, old_html, ok: bool) -> None:
        if not ok:
            return
        try:
            WebDriverWait(self.driver, 8).until(EC.staleness_of(old_html))
        except TimeoutException:
            pass
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=5)

    def check_out(self) -> tuple[bool, str]:
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        ok, msg = self.do("check out", "yes")
        self._wait_reload_after_action(old_html, ok)
        return ok, msg

    def cancel_check_out(self) -> tuple[bool, str]:
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        ok, msg = self.do("cancel check out", "yes")
        self._wait_reload_after_action(old_html, ok)
        return ok, msg

    def is_in_checked_out_list(self, name: str, timeout: int = 8) -> bool:
        self.driver.get(cfg.CHECKOUT_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=6)
        low = name.lower()
        try:
            return WebDriverWait(self.driver, timeout, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda d: any(low in (r.text or "").lower() for r in d.find_elements(By.CSS_SELECTOR, "table tbody tr"))
            )
        except TimeoutException:
            return False

    def download_current(self) -> str | None:
        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        started = time.time()
        self.click_label("download")
        return self.wait_for_download(before, started=started)

    def open_full_view_tab(self) -> str:
        old_tabs = list(self.driver.window_handles)
        self.click_label("view")
        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > len(old_tabs))
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.wait_for_page_load()
        return self.driver.current_url

    def archive(self) -> tuple[bool, str]:
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        ok, msg = self.do("archive", "yes")
        self._wait_reload_after_action(old_html, ok)
        return ok, msg

    def restore_archived(self) -> tuple[bool, str]:
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        label = "restore archive" if self.find_by_label("restore archive") is not None else "restore"
        ok, msg = self.do(label, "yes")
        self._wait_reload_after_action(old_html, ok)
        return ok, msg

    def delete_current(self) -> tuple[bool, str]:
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        ok, msg = self.do("delete", "yes")
        self._wait_reload_after_action(old_html, ok)
        return ok, msg

    
    # Related Files (DMS-TC030, TC031)
    

    def link_related_file(self, other_name: str) -> tuple[bool, str]:
        self.click(self.wait.until(EC.element_to_be_clickable(self.RELATED_BTN)))
        modal = self.wait.until(EC.visibility_of_element_located(self.ADD_RELATED_MODAL))
        self.wait_for_ajax_idle(timeout=5)

        inputs = [i for i in modal.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']") if i.is_displayed()]
        if inputs:
            inputs[0].clear()
            inputs[0].send_keys(other_name, Keys.ENTER)
            self.wait_for_ajax_idle(timeout=5)

        item = self.wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                f"//div[@id='addRelated']//*[self::tr or self::li or contains(@class, 'list-group-item')]"
                f"[contains(., {self.xpath_text(other_name)})]",
            ))
        )
        self.driver.execute_script("""
            var item = arguments[0];
            var cb = item.querySelector("input[type='checkbox']");
            if (cb && !cb.checked) {
                var lbl = cb.id ? document.querySelector("label[for='" + cb.id + "']") : null;
                if (lbl) lbl.click(); else cb.click();
                if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change', {bubbles: true})); }
            } else if (!cb) {
                item.click();
            }
        """, item)
        link_btn = modal.find_element(By.CSS_SELECTOR, "button[data-type='addLinkedFile']")
        return self.message_after(lambda: self.click(link_btn))

    def expand_related_panel(self) -> None:
        self.wait_for_ajax_idle(timeout=5)
        self.driver.execute_script("""
            var btn = document.querySelector("button[data-type='related']");
            if (btn) {
                var card = btn.closest('.card, .panel') || btn.parentElement.parentElement;
                if (card) {
                    var toggle = card.querySelector('[data-toggle="collapse"], .card-header a, .card-header');
                    if (toggle && !card.querySelector('.collapse.in, .collapse.show')) toggle.click();
                    card.querySelectorAll('.collapse').forEach(function(c) {
                        c.classList.add('in', 'show');
                        c.style.display = 'block';
                        c.style.height = 'auto';
                    });
                }
            }
        """)
        self.wait_for_ajax_idle(timeout=4)

    def is_related_shown(self, name: str) -> bool:
        self.expand_related_panel()
        low = name.lower()
        try:
            return WebDriverWait(self.driver, 8).until(
                lambda d: any(
                    el.is_displayed() and low in (el.text or "").lower()
                    for el in d.find_elements(By.CSS_SELECTOR, "#relatedFiles a[data-action='viewPreview'], #relatedFiles .list-group-item")
                )
            )
        except TimeoutException:
            return False

    def view_related_file(self, other_name: str) -> tuple[bool, str]:
        self.expand_related_panel()
        links = [
            el for el in self.driver.find_elements(By.CSS_SELECTOR, "#relatedFiles a[data-action='viewPreview']")
            if el.is_displayed() and other_name.lower() in (el.text or "").lower()
        ]
        if not links:
            return False, f"related file link '{other_name}' not found in #relatedFiles"
        self.click(links[0])
        try:
            result = WebDriverWait(self.driver, 10).until(
                lambda d: any(
                    m.is_displayed()
                    and bool(
                        m.find_elements(
                            By.CSS_SELECTOR,
                            ".modal-preview iframe[src], .modal-preview img[src], "
                            ".modal-preview object[data], .modal-preview audio[src], "
                            ".modal-preview video[src], .ver-modal-preview table, .modal-preview h2",
                        )
                    )
                    for m in d.find_elements(By.ID, "viewFile")
                )
            )
        except TimeoutException:
            return False, f"related file preview modal (#viewFile) did not open with content for '{other_name}'"
        close_btns = self.visible("#viewFile button.close, #viewFile [data-dismiss='modal']")
        if close_btns:
            self.click(close_btns[0])
            try:
                WebDriverWait(self.driver, 5).until(EC.invisibility_of_element_located((By.ID, "viewFile")))
            except TimeoutException:
                pass
        return bool(result), f"Related file '{other_name}' preview opened in #viewFile"

    def _related_panel_text(self) -> str:
        return (
            self.driver.execute_script(
                "var el = document.getElementById('relatedFiles'); return el ? (el.innerText || '') : '';"
            )
            or ""
        ).lower()

    def wait_related_removed(self, name: str, timeout: int = 8) -> bool:
        self.expand_related_panel()
        try:
            WebDriverWait(self.driver, timeout).until(lambda _d: name.lower() not in self._related_panel_text())
            return True
        except TimeoutException:
            return False

    def unlink_related_file(self, other_name: str) -> tuple[bool, str]:
        self.expand_related_panel()
        del_btn = self.driver.execute_script("""
            var name = arguments[0].toLowerCase();
            var root = document.getElementById('relatedFiles');
            if (!root) return null;
            var rows = Array.from(root.querySelectorAll('a.list-group-item, div.list-group-item, tr, li')).filter(function(el) {
                return (el.innerText || '').toLowerCase().indexOf(name) !== -1;
            });
            rows.sort(function(a, b) { return (a.innerText || '').length - (b.innerText || '').length; });
            var row = rows[0];
            if (!row) return null;
            var scope = row.parentElement || row;
            return scope.querySelector('#del_link, [onclick*="delete"], .zmdi-delete, .fa-trash') || row.querySelector('#del_link');
        """, other_name)

        old_html = self.driver.find_element(By.TAG_NAME, "html")
        if del_btn is None:
            del_btns = [b for b in self.driver.find_elements(By.CSS_SELECTOR, "#relatedFiles #del_link") if b.is_displayed()]
            if not del_btns:
                return False, f"unlink icon (#del_link) not found for '{other_name}'"
            del_btn = del_btns[0]

        def _action():
            self.click(del_btn)
            if not self.confirm_any(("unlink", "yes", "delete", "ok")):
                raise AssertionError("Unlink confirmation dialog ('Yes, Unlink!') did not appear")

        ok, msg = self.message_after(_action)
        if ok:
            self._wait_reload_after_action(old_html, True)
        return ok, msg

    
    # Share Section & Email Share (DMS-TC033, TC034, TC036)
    

    def expand_share_section(self) -> None:
        self.wait_for_ajax_idle(timeout=5)
        panels = self.driver.find_elements(*self.SHARE_PANEL)
        classes = (panels[0].get_attribute("class") or "").split() if panels else []
        if not panels or ("in" not in classes and "collapsing" not in classes):
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "[href='#share_document'], #document-share-id .card-header"
            )
            if headers:
                self.click(headers[0])
            else:
                self.driver.execute_script("""
                    document.querySelectorAll('.card-header, .panel-heading, a, div').forEach(function(el) {
                        var t = (el.innerText || '').trim().toLowerCase();
                        if (t === 'share document(s)' || t === 'share documents' || t === 'share') el.click();
                    });
                """)

        try:
            WebDriverWait(self.driver, 8).until(
                lambda d: any(
                    "in" in (p.get_attribute("class") or "").split()
                    and "collapsing" not in (p.get_attribute("class") or "").split()
                    and p.is_displayed()
                    for p in d.find_elements(*self.SHARE_PANEL)
                )
            )
        except TimeoutException:
            pass

        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: not any(
                    el.is_displayed() for el in d.find_elements(By.CSS_SELECTOR, "#document-share-id #loaderOverlay")
                )
            )
        except TimeoutException:
            pass

        self.wait_for_ajax_idle(timeout=5)

    def shared_participants_values(self) -> list[str]:
        self.expand_share_section()
        vals = self.driver.execute_script(
            "var v = window.$ && $('#shared_docs').val(); return v ? (Array.isArray(v) ? v : [v]) : [];"
        )
        return [str(x) for x in (vals or []) if str(x)]

    def share_on_document_view(self, kind: str) -> tuple[bool, str, str]:
        self.expand_share_section()

        def _option_ready(d) -> bool:
            if self.visible("#document-share-id #loaderOverlay"):
                return False
            return bool(d.execute_script("""
                var s = document.getElementById('shared_docs');
                if (!s) return false;
                var kind = (arguments[0] || '').toLowerCase();
                if (kind === 'public') return !!s.querySelector("option[value='all-1']");
                if (kind === 'all users') return !!s.querySelector("option[value='all-2']");
                var groups = s.querySelectorAll('optgroup');
                for (var i = 0; i < groups.length; i++) {
                    if ((groups[i].label || '').toLowerCase() === kind && groups[i].querySelector('option')) return true;
                }
                return false;
            """, kind))

        WebDriverWait(self.driver, 15).until(_option_ready)
        picked = self.driver.execute_script("""
            var s = document.getElementById('shared_docs'); var picked = '';
            var kind = (arguments[0] || '').toLowerCase();
            if (kind === 'public') { var o = s.querySelector("option[value='all-1']"); if (o) { o.selected = true; picked = o.text.trim(); } }
            else if (kind === 'all users') { var o = s.querySelector("option[value='all-2']"); if (o) { o.selected = true; picked = o.text.trim(); } }
            else {
                s.querySelectorAll('optgroup').forEach(function(g) {
                    if ((g.label || '').toLowerCase() === kind && !picked) {
                        var o = g.querySelector('option');
                        if (o) { o.selected = true; picked = o.text.trim(); }
                    }
                });
            }
            if (window.$) $(s).trigger('change');
            return picked;
        """, kind)
        if not picked:
            return False, f"no '{kind}' option in #shared_docs", ""

        old_html = self.driver.find_element(By.TAG_NAME, "html")
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "submit_share_document")))

        if kind.lower() == "public":
            self.click(submit_btn)
            link_input = self.wait.until(EC.visibility_of_element_located((By.ID, "share_document_generated_link")))
            share_url = (link_input.get_attribute("value") or "").strip()
            if not self.confirm_any(("copy url", "yes", "ok")):
                return False, "Copy URL modal confirm button did not appear", share_url
            return True, f"Shared as '{picked}' with link '{share_url}'", share_url

        ok, msg = self.message_after(lambda: self.click(submit_btn), seconds=15)
        if not ok:
            return False, msg, ""
        self._wait_reload_after_action(old_html, True)
        persisted = bool(self.shared_participants_values())
        if not persisted:
            return False, f"{msg}, but shared participant did not persist in #shared_docs after reload", ""
        return True, f"{msg} ('{picked}' persisted in #shared_docs)", ""

    def read_share_link_input(self) -> str:
        self.expand_share_section()
        el = self.wait.until(EC.presence_of_element_located((By.ID, "generated_link_for_share")))
        return (el.get_attribute("value") or "").strip()

    def _find_share_delete_btn(self):
        for el in self.driver.find_elements(By.CSS_SELECTOR, self.SHARE_DELETE_SELECTORS):
            if el.is_displayed() and el.is_enabled():
                return el
        return None

    def delete_shared_participant(self) -> tuple[bool, str]:
        self.expand_share_section()
        if not self.shared_participants_values():
            return False, "#shared_docs has no shared participant selected to delete"
        try:
            del_btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_share_delete_btn())
        except TimeoutException:
            return False, "Could not find the Delete button (#delete_share_document) under Share Document(s)"

        old_html = self.driver.find_element(By.TAG_NAME, "html")

        def _action():
            self.click(del_btn)
            self.confirm_any(("yes", "delete", "remove", "ok"))

        ok, msg = self.message_after(_action, seconds=15)
        if not ok:
            return False, msg

        self._wait_reload_after_action(old_html, True)
        remaining = self.shared_participants_values()
        if remaining:
            return False, f"{msg}, but #shared_docs still has selected participants: {remaining}"
        return True, f"{msg}. Shared participants cleared"

    def share_by_email(
        self,
        email: str,
        subject: str = "AUTO share test",
        body_text: str = "Please find the shared document attached.",
    ) -> tuple[bool, str]:
        self.expand_share_section()
        email_btn = self.driver.find_element(*self.EMAIL_SHARE_BTN)
        if not email_btn.is_displayed():
            self.click(self.driver.find_element(By.CSS_SELECTOR, "#document-share-id .card-header"))
            self.wait.until(EC.visibility_of(email_btn))

        self.driver.execute_script("""
            var s = document.getElementById('shared_docs');
            if (s) {
                var opt = s.querySelector('optgroup[label="Users"] option') || s.querySelector('option[value="all-2"]');
                if (opt) opt.selected = true;
                if (window.$) $(s).trigger('change');
            }
        """)

        self.click(email_btn)
        modal = self.wait.until(EC.visibility_of_element_located(self.EMAIL_SHARE_MODAL))
        self.wait_for_ajax_idle(timeout=5)

        s2_inputs = modal.find_elements(By.CSS_SELECTOR, "input.select2-search__field")
        if s2_inputs and s2_inputs[0].is_displayed():
            s2_inputs[0].send_keys(email, Keys.ENTER)
        else:
            self.driver.execute_script("""
                var to = document.getElementById('to');
                if (to) {
                    to.appendChild(new Option(arguments[0], arguments[0], true, true));
                    if (window.$) $(to).trigger('change');
                }
            """, email)

        subj = modal.find_element(By.ID, "subject")
        if not (subj.get_attribute("value") or "").strip():
            subj.clear()
            subj.send_keys(subject)

        body = modal.find_element(By.ID, "body")
        if not (body.get_attribute("value") or "").strip():
            body.send_keys(body_text)

        WebDriverWait(self.driver, 8).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#attachment option")) > 0
        )
        selected_count = self.driver.execute_script("""
            var att = document.getElementById('attachment');
            var count = 0;
            if (att && att.options.length > 0) {
                for (var i = 0; i < att.options.length; i++) {
                    if (att.options[i].value) { att.options[i].selected = true; count++; }
                }
                if (window.$) {
                    if ($.fn.selectpicker) $(att).selectpicker('refresh');
                    $(att).trigger('change');
                }
            }
            return count;
        """)
        to_vals = self.driver.execute_script("return $('#to').val() || [];")
        if not to_vals or not (subj.get_attribute("value") or "").strip() or not selected_count:
            return False, f"email modal missing fields (to={to_vals}, attachments={selected_count})"

        send_btn = self.driver.find_element(By.ID, "send_email_share_document_modal")
        ok, message = self.message_after(lambda: self.click(send_btn))
        return ok, f"{message} (to={email}, attachments={selected_count})"

    # ------------------------------------------------------------------
    # OCR Status & Ask Effy AI Chat (DMS-TC037, TC136, TC137, TC139)
    # ------------------------------------------------------------------

    def expand_system_metadata(self) -> None:
        panel = self.driver.find_elements(*self.SYSTEM_META_BODY)
        if panel and "in" not in (panel[0].get_attribute("class") or "").split():
            toggle = self.driver.find_elements(
                By.CSS_SELECTOR, "[data-target='#systemDefinedMetaDataBody'], #systemDefinedMetaDataBodyHeadingOne a"
            )
            if toggle:
                self.click(toggle[0])
                try:
                    WebDriverWait(self.driver, 5).until(lambda _d: panel[0].is_displayed())
                except TimeoutException:
                    pass

    def read_ocr_status(self) -> str:
        els = self.driver.find_elements(*self.OCR_STATUS)
        if not els:
            return ""
        return (els[0].text or els[0].get_attribute("textContent") or "").strip()

    def wait_for_ocr_status(self, timeout_seconds: int = 60) -> tuple[bool, str]:
        deadline = time.time() + timeout_seconds
        current = ""
        while time.time() < deadline:
            self.wait_for_page_load()
            self.expand_system_metadata()
            current = self.read_ocr_status()
            if current.strip().lower() == "done":
                return True, f"OCR Status: {current}"
            time.sleep(min(5.0, max(0.5, deadline - time.time())))
            if time.time() < deadline:
                self.driver.refresh()
        return False, f"OCR did not complete within {timeout_seconds}s (OCR Status: {current or 'missing'})"

    def ask_effy_chat(self, question: str = "What is this document about?", timeout_seconds: int = 60) -> tuple[bool, str]:
        self.wait_for_page_load()
        chat_box = self.wait.until(EC.element_to_be_clickable(self.AI_CHAT_INPUT))
        before_answers = len(
            self.driver.find_elements(By.CSS_SELECTOR, ".list-ai-group > div[style*='#f9f9fe'] p")
        )
        self.click(chat_box)
        chat_box.clear()
        chat_box.send_keys(question)

        try:
            submit_btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(self.AI_CHAT_SUBMIT))
        except TimeoutException:
            self.click(chat_box)
            submit_btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.AI_CHAT_SUBMIT))
        self.click(submit_btn)

        def _done(d):
            if d.find_elements(By.ID, "chat-gif"):
                return False
            btn = d.find_elements(*self.AI_CHAT_SUBMIT)
            if btn and not btn[0].is_enabled():
                return False
            err_popup = self.popup_text()
            if err_popup and any(w in err_popup.lower() for w in self.ERROR_WORDS):
                return ("error", err_popup)
            answers = d.find_elements(By.CSS_SELECTOR, ".list-ai-group > div[style*='#f9f9fe'] p")
            if len(answers) > before_answers:
                txt = (answers[-1].text or "").strip()
                if txt:
                    return ("answer", txt)
            return False

        try:
            kind, payload = WebDriverWait(self.driver, timeout_seconds, poll_frequency=1).until(_done)
        except TimeoutException:
            return False, f"no answer from the AI within {timeout_seconds} seconds"

        if kind == "error":
            return False, f"AI chat error: {payload}"
        low = payload.lower()
        if any(err in low for err in ("something went wrong", "unable to", "error occurred")):
            return False, f"AI returned error message: {payload[:120]}"
        return True, f"AI answered: {payload[:140]}"
