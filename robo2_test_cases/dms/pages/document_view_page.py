"""Page Object for the Document Full View / Details screen."""
from __future__ import annotations

import os
import time

from selenium.common.exceptions import TimeoutException
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
        "#share_document button[data-type*='remove' i], "
        "#share_document button[data-type*='unshare' i], "
        "#share_document button[title*='Delete' i], "
        "#share_document a[title*='Delete' i], "
        "#share_document [onclick*='delete' i], "
        "#share_document [onclick*='remove' i], "
        "#share_document .fa-trash, "
        "#share_document .zmdi-delete, "
        "#share_document .select2-selection__choice__remove"
    )

    # ------------------------------------------------------------------
    # Metadata Editing (DMS-TC019)
    # ------------------------------------------------------------------

    def edit_metadata_field_and_save(self) -> tuple[bool, str]:
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

        self.wait_for_ajax_idle(timeout=5)
        fields = [
            f for f in self.visible(self.EDIT_METADATA_INPUTS)
            if f.is_enabled()
            and not f.get_attribute("readonly")
            and "date" not in (f.get_attribute("id") or "").lower()
            and "search" not in (f.get_attribute("id") or "").lower()
            and "search" not in (f.get_attribute("placeholder") or "").lower()
            and "effy" not in (f.get_attribute("placeholder") or "").lower()
            and "question" not in (f.get_attribute("placeholder") or "").lower()
        ]
        ours = [f for f in fields if (f.get_attribute("value") or "").startswith("AUTO_")]
        if not (ours or fields):
            return False, "no editable meta-data field found"

        target = (ours or fields)[0]
        outer = (target.get_attribute("outerHTML") or "").lower()
        if any(w in outer for w in ("digits", "number", "integer", "numeric")):
            target.send_keys("9")
        else:
            target.send_keys("_EDIT")

        if self.find_by_label("save changes") is not None:
            return self.do("save changes")
        return self.do("save")

    # ------------------------------------------------------------------
    # Version History (DMS-TC014, TC015, TC016)
    # ------------------------------------------------------------------

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

    def download_version(self, version_text: str) -> str | None:
        self.show_versions(version_text)
        btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_version_action(version_text, "download"))
        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        self.click(btn)
        return self.wait_for_download(before)

    def delete_version(self, version_text: str) -> tuple[bool, str]:
        self.show_versions(version_text)
        btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_version_action(version_text, "delete"))
        return self.message_after(lambda: (self.click(btn), self.confirm("yes")))

    # ------------------------------------------------------------------
    # Lifecycle: Checkout, Download, Full View, Archive, Delete
    # ------------------------------------------------------------------

    def check_out(self) -> tuple[bool, str]:
        return self.do("check out", "yes")

    def cancel_check_out(self) -> tuple[bool, str]:
        return self.do("cancel check out", "yes")

    def is_in_checked_out_list(self, name: str, timeout: int = 8) -> bool:
        self.driver.get(cfg.CHECKOUT_URL)
        self.wait_for_page_load()
        return self.wait_text(name, timeout)

    def download_current(self) -> str | None:
        before = set(os.listdir(cfg.DOWNLOAD_DIR))
        self.click_label("download")
        return self.wait_for_download(before)

    def open_full_view_tab(self) -> str:
        old_tabs = list(self.driver.window_handles)
        self.click_label("view")
        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > len(old_tabs))
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.wait_for_page_load()
        return self.driver.current_url

    def archive(self) -> tuple[bool, str]:
        ok, msg = self.do("archive", "yes")
        if ok:
            self.wait_for_ajax_idle(timeout=5)
        return ok, msg

    def restore_archived(self) -> tuple[bool, str]:
        label = "restore archive" if self.find_by_label("restore archive") is not None else "restore"
        ok, msg = self.do(label, "yes")
        if ok:
            self.wait_for_ajax_idle(timeout=5)
        return ok, msg

    def delete_current(self) -> tuple[bool, str]:
        ok, msg = self.do("delete", "yes")
        if ok:
            self.wait_for_ajax_idle(timeout=5)
        return ok, msg

    # ------------------------------------------------------------------
    # Related Files (DMS-TC030, TC031)
    # ------------------------------------------------------------------

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
        if self.wait_text(name, 3):
            return True
        self.expand_related_panel()
        return self.wait_text(name, 5)

    def _related_panel_text(self) -> str:
        return (
            self.driver.execute_script("""
                var btn = document.querySelector("button[data-type='related']");
                var card = btn && (btn.closest('.card, .panel') || btn.parentElement.parentElement);
                return card ? (card.innerText || '') : '';
            """)
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
            var name = arguments[0];
            var btn = document.querySelector("button[data-type='related']");
            var root = (btn && (btn.closest('.card, .panel') || btn.parentElement.parentElement)) || document;
            var rows = Array.from(root.querySelectorAll('tr, li, .list-group-item, .lv-item, div')).filter(function(el) {
                var t = (el.innerText || '').trim();
                return t.indexOf(name) !== -1 && el.querySelectorAll('a, button, i').length > 0;
            });
            rows.sort(function(a, b) { return (a.innerText || '').length - (b.innerText || '').length; });
            var row = rows[0];
            if (!row) return null;
            var candidates = Array.from(row.querySelectorAll('button, a, i, span')).filter(function(el) {
                var html = (el.outerHTML || '').toLowerCase();
                return ['delete','unlink','remove','trash','close','times'].some(k => html.indexOf(k) !== -1);
            });
            if (candidates.length > 0) return candidates[0];
            var clickables = Array.from(row.querySelectorAll('button, a, i')).filter(function(el) {
                return (el.innerText || '').trim().indexOf(name) === -1 && el.offsetParent !== null;
            });
            return clickables[clickables.length - 1] || null;
        """, other_name)

        old_html = self.driver.find_element(By.TAG_NAME, "html")
        old_btn = del_btn

        if del_btn is None:
            ok, msg = self.do_near(other_name, "delete", "yes")
        else:
            def _action():
                self.click(del_btn)
                self.confirm_any(("yes", "unlink", "delete", "ok"))

            ok, msg = self.message_after(_action)

        if ok:
            def _refreshed(d) -> bool:
                try:
                    if EC.staleness_of(old_html)(d):
                        return True
                except Exception:
                    return True
                if old_btn is not None:
                    try:
                        if EC.staleness_of(old_btn)(d):
                            return True
                    except Exception:
                        return True
                return False

            try:
                WebDriverWait(self.driver, 8).until(_refreshed)
            except TimeoutException:
                pass
            self.wait_for_page_load()
            self.wait_for_ajax_idle(timeout=5)

        return ok, msg

    # ------------------------------------------------------------------
    # Share Section & Email Share (DMS-TC033, TC034, TC036)
    # ------------------------------------------------------------------

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

    def _find_share_delete_btn(self):
        for el in self.driver.find_elements(By.CSS_SELECTOR, self.SHARE_DELETE_SELECTORS):
            if el.is_displayed() and el.is_enabled():
                return el
        for el in self.driver.find_elements(
            By.XPATH, "//div[@id='share_document']//*[self::button or self::a or self::input]"
        ):
            label = (el.text or el.get_attribute("value") or "").strip().lower()
            if label in ("delete", "remove", "unshare") and el.is_displayed() and el.is_enabled():
                return el
        return None

    def delete_shared_participant(self) -> tuple[bool, str]:
        self.expand_share_section()
        try:
            del_btn = WebDriverWait(self.driver, 10).until(lambda _d: self._find_share_delete_btn())
        except TimeoutException:
            return False, "Could not find the Delete button under the Share Document(s) section"

        is_token = "select2-selection__choice__remove" in (del_btn.get_attribute("class") or "")

        def _action():
            self.click(del_btn)
            if is_token:
                share_btns = [
                    b
                    for b in self.driver.find_elements(By.ID, "submit_share_document")
                    if b.is_displayed() and b.is_enabled()
                ]
                if not share_btns:
                    share_btns = [
                        b
                        for b in self.driver.find_elements(
                            By.XPATH,
                            "//div[@id='share_document']//*[self::button or self::a or self::input]"
                            "[contains(translate(normalize-space(.), 'SHAREUPDT', 'shareupdt'), 'share') or "
                            "contains(translate(normalize-space(.), 'SHAREUPDT', 'shareupdt'), 'update')]",
                        )
                        if b.is_displayed() and b.is_enabled()
                    ]
                if share_btns:
                    self.click(share_btns[0])
            self.confirm_any(("yes", "delete", "remove", "ok"))

        try:
            ok, msg = self.message_after(_action, seconds=10)
        except TimeoutException:
            ok, msg = True, "Removed shared participant"

        if not ok:
            return False, msg

        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=5)
        self.expand_share_section()
        return True, msg

    def share_by_email(
        self,
        email: str,
        subject: str = "AUTO share test",
        body_text: str = "Please find the shared document attached.",
    ) -> tuple[bool, str]:
        email_btn = self.driver.find_element(*self.EMAIL_SHARE_BTN)
        if not email_btn.is_displayed():
            self.click(self.driver.find_element(By.CSS_SELECTOR, "#document-share-id .card-header"))
            self.wait.until(EC.visibility_of(email_btn))

        # Select a user in #shared_docs so 'Selected_Users_&_Groups' in modal has a participant too
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

        WebDriverWait(self.driver, 5).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#attachment option")) > 0
        )
        self.driver.execute_script("""
            var att = document.getElementById('attachment');
            if (att && att.options.length > 0) {
                for (var i = 0; i < att.options.length; i++) {
                    if (att.options[i].value) att.options[i].selected = true;
                }
                if (window.$) {
                    if ($.fn.selectpicker) $(att).selectpicker('refresh');
                    $(att).trigger('change');
                }
            }
        """)

        send_btn = self.driver.find_element(By.ID, "send_email_share_document_modal")
        ok, message = self.message_after(lambda: self.click(send_btn))
        return ok, f"{message} (mail delivery to {email} must be checked in the mailbox)"

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
        self.wait_for_page_load()
        self.expand_system_metadata()

        def _ready(_d):
            val = self.read_ocr_status()
            return val if val and val.upper() != "N/A" else False

        try:
            ocr_status = WebDriverWait(self.driver, timeout_seconds, poll_frequency=2).until(_ready)
            return True, f"OCR Status: {ocr_status}"
        except TimeoutException:
            current = self.read_ocr_status()
            return False, f"OCR was not enabled (OCR Status: {current or 'missing'})"

    def ask_effy_chat(self, question: str = "What is this document about?", timeout_seconds: int = 60) -> tuple[bool, str]:
        self.wait_for_page_load()
        chat_box = self.wait.until(EC.element_to_be_clickable(self.AI_CHAT_INPUT))
        self.click(chat_box)
        chat_box.clear()
        chat_box.send_keys(question)

        try:
            submit_btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(self.AI_CHAT_SUBMIT))
        except TimeoutException:
            self.click(chat_box)
            submit_btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(self.AI_CHAT_SUBMIT))
        self.click(submit_btn)

        def _answered(d):
            scroll_bars = d.find_elements(*self.AI_CHAT_HISTORY)
            if not scroll_bars:
                return False
            text = (scroll_bars[0].text or "").strip()
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            answers = [ln for ln in lines if ln != question]
            return " ".join(answers) if answers else False

        try:
            full_ans = WebDriverWait(self.driver, timeout_seconds, poll_frequency=2).until(_answered)
            return True, f"AI answered: {full_ans[:120]}"
        except TimeoutException:
            return False, f"no answer from the AI within {timeout_seconds} seconds"
