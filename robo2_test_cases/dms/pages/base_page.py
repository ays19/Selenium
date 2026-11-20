"""Reusable Selenium BasePage with explicit-wait UI primitives for DMS."""
from __future__ import annotations

import os
import re
import time

from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

import dms_config as cfg


class SetupError(Exception):
    """Raised when test prerequisites or setup data cannot be prepared."""


class BasePage:
    """Base Page Object providing shared Selenium waits, clicks, modals, and Select2 helpers."""

    BODY_LOCATOR = (By.TAG_NAME, "body")
    FILE_INPUT = (By.CSS_SELECTOR, "input[type='file']")
    LOADING_INDICATORS = (
        By.CSS_SELECTOR,
        ".dataTables_processing, .ant-spin-spinning, .loading-spinner",
    )
    MESSAGE_BOX = (
        ".toast, .alert, .swal2-popup, [role='alert'], .snackbar, .Toastify__toast, "
        ".mat-snack-bar-container, .ant-message, .growl-animated, [data-notify], [data-growl='container']"
    )
    SUCCESS_WORDS = (
        "success", "uploaded", "saved", "archived", "restored", "deleted", "created",
        "updated", "checked", "linked", "unlinked", "shared", "sent", "added", "removed",
        "published", "assigned", "cloned", "enabled", "disabled", "approved", "rejected", "downloaded",
    )
    ERROR_WORDS = (
        "error", "failed", "required", "already exists", "invalid", "no checker", "you can only",
    )

    LOWER = "translate({0}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ-_', 'abcdefghijklmnopqrstuvwxyz  ')"
    MODAL = (
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' modal ') "
        "and (contains(concat(' ', normalize-space(@class), ' '), ' in ') or contains(@class, 'show'))]"
    )
    CLICKABLE = "self::a or self::button or self::i or self::span or self::li or self::label or self::td or self::div"
    FIELD_XPATH = (
        "following::*[(self::input or self::textarea or self::select) "
        "and not(ancestor::*[contains(@class, 'bs-searchbox')]) "
        "and not(contains(@class, 'select2-search__field'))][1]"
    )

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ------------------------------------------------------------------
    # Text & Page Wait Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def xpath_text(text: str) -> str:
        """Safely quote text for an XPath expression, including apostrophes."""
        text = str(text)
        if "'" not in text:
            return f"'{text}'"
        if '"' not in text:
            return f'"{text}"'
        parts = text.split("'")
        return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"

    @staticmethod
    def clean(text: str | None) -> str:
        return re.sub(r"[*:]", "", text or "").strip().lower()

    def wait_for_page_load(self) -> None:
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def wait_for_ajax_idle(self, timeout: int = 10) -> None:
        """Wait for visible spinners and active jQuery AJAX calls to settle."""
        def _is_idle(d) -> bool:
            if self.visible(self.LOADING_INDICATORS[1]):
                return False
            try:
                return bool(d.execute_script("return !window.jQuery || window.jQuery.active === 0;"))
            except Exception:
                return True

        try:
            WebDriverWait(self.driver, timeout).until(_is_idle)
        except TimeoutException:
            pass

    def body_text(self) -> str:
        for _ in range(3):
            try:
                return self.driver.find_element(*self.BODY_LOCATOR).text.lower()
            except StaleElementReferenceException:
                time.sleep(0.15)
        return ""

    def visible(self, css: str) -> list:
        result = []
        for elem in self.driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if elem.is_displayed():
                    result.append(elem)
            except StaleElementReferenceException:
                continue
        return result

    def wait_text(self, text: str, seconds: int = 8) -> bool:
        try:
            WebDriverWait(self.driver, seconds).until(lambda _d: text.lower() in self.body_text())
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Click & Label Lookup
    # ------------------------------------------------------------------

    def click(self, element) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def predicate(self, label: str, exact: bool) -> str:
        text = label.lower().replace("-", " ").replace("_", " ")
        fields = [
            self.LOWER.format("normalize-space(.)"),
            self.LOWER.format("normalize-space(@title)"),
            self.LOWER.format("normalize-space(@data-original-title)"),
            self.LOWER.format("normalize-space(@aria-label)"),
            self.LOWER.format("normalize-space(@value)"),
        ]
        if exact:
            return "[" + " or ".join(f"{f} = {self.xpath_text(text)}" for f in fields) + "]"
        return "[" + " or ".join(f"contains({f}, {self.xpath_text(text)})" for f in fields) + "]"

    def find_by_label(self, label: str, root=None, slack: int = 25):
        """Find the first visible button, icon, or link matching label (checks open modals first)."""
        if root is None:
            low = label.lower()
            if low in ("save changes", "save"):
                update_btns = self.visible("#editMeta button[data-type='updateMeta']")
                if update_btns:
                    return update_btns[0]
            if low == "download":
                dl_btns = [
                    b for b in self.visible("#search_modal button.search_result_download")
                    if b.is_enabled()
                ]
                if dl_btns:
                    return dl_btns[0]
                if self.visible("#requested_downloads"):
                    links = self.visible("#requested_downloads tbody a[href]")
                    return links[0] if links else None
            if self.visible("#search_modal"):
                rows = self.driver.find_elements(
                    By.XPATH, f"//div[@id='search_modal']//tr[contains(., {self.xpath_text(label)})]"
                )
                for row in rows:
                    if row.is_displayed():
                        open_icons = [
                            el for el in row.find_elements(
                                By.XPATH,
                                ".//*[contains(@class, 'openInNew') or contains(@title, 'Open') or contains(@data-original-title, 'Open')] | "
                                ".//td[last()]//*[self::a or self::button or self::i]",
                            )
                            if el.is_displayed()
                        ]
                        if open_icons:
                            return open_icons[-1]
            three_dot = self.visible("#three-dot > li.dropdown > a")
            menu = self.driver.find_elements(By.CSS_SELECTOR, "#three-dot ul.dropdown-menu")
            if three_dot and menu:
                items = menu[0].find_elements(By.XPATH, f".//a{self.predicate(label, False)}")
                if items:
                    if not menu[0].is_displayed():
                        self.click(three_dot[0])
                        try:
                            WebDriverWait(self.driver, 3).until(lambda _d: any(i.is_displayed() for i in items))
                        except TimeoutException:
                            pass
                    visible_items = [e for e in items if e.is_displayed()]
                    if visible_items:
                        return visible_items[0]

        scopes = [None] if root is not None else [self.MODAL, ""]
        for scope in scopes:
            for exact in (True, False):
                try:
                    if root is not None:
                        candidates = root.find_elements(
                            By.XPATH, f".//*[{self.CLICKABLE}]{self.predicate(label, exact)}"
                        )
                    else:
                        candidates = self.driver.find_elements(
                            By.XPATH, f"{scope}//*[{self.CLICKABLE}]{self.predicate(label, exact)}"
                        )
                except StaleElementReferenceException:
                    continue
                for elem in candidates:
                    try:
                        if elem.is_displayed() and len(elem.text.strip()) <= len(label) + slack:
                            return elem
                    except StaleElementReferenceException:
                        continue
        return None

    def find_near(self, anchor_text: str, label: str):
        try:
            anchor = self.find_by_label(anchor_text, slack=300)
            if anchor is None:
                return None
            container = anchor.find_element(
                By.XPATH, f"ancestor::*[.//*[{self.CLICKABLE}]{self.predicate(label, False)}][1]"
            )
            return self.find_by_label(label, root=container)
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def _retry_lookup(self, lookup_fn, action_fn):
        for attempt in range(3):
            try:
                element = WebDriverWait(
                    self.driver,
                    10,
                    ignored_exceptions=(NoSuchElementException, StaleElementReferenceException),
                ).until(lookup_fn)
                return action_fn(element)
            except StaleElementReferenceException:
                if attempt == 2:
                    raise
                time.sleep(0.3)

    def click_label(self, label: str, slack: int = 25):
        def _act(element):
            action = element.get_attribute("data-action") or ""
            self.click(element)
            if action == "editMeta":
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.ID, "editMeta"))
                    )
                except TimeoutException:
                    pass
            return element

        return self._retry_lookup(lambda _d: self.find_by_label(label, slack=slack), _act)

    def click_near(self, anchor_text: str, label: str):
        return self._retry_lookup(
            lambda _d: self.find_near(anchor_text, label),
            lambda el: (self.click(el), el)[1],
        )

    def double_click_label(self, label: str) -> None:
        def _act(element):
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            ActionChains(self.driver).double_click(element).perform()

        self._retry_lookup(lambda _d: self.find_by_label(label), _act)

    # ------------------------------------------------------------------
    # Popups, Notifications & Modals
    # ------------------------------------------------------------------

    def popup_text(self) -> str:
        boxes = []
        for elem in self.driver.find_elements(By.CSS_SELECTOR, self.MESSAGE_BOX):
            try:
                if elem.is_displayed():
                    txt = elem.text.strip()
                    if txt:
                        boxes.append(txt)
            except StaleElementReferenceException:
                continue
        return " | ".join(boxes)

    def wait_for_message(self, text_before: str, seconds: int = 20) -> tuple[bool, str]:
        def _new_message(d):
            boxes = []
            for elem in d.find_elements(By.CSS_SELECTOR, self.MESSAGE_BOX):
                try:
                    if elem.is_displayed():
                        txt = elem.text.strip()
                        if txt:
                            boxes.append(txt)
                except StaleElementReferenceException:
                    continue
            try:
                saved = d.execute_script("return sessionStorage.getItem('__last_notify_msg') || '';")
            except Exception:
                saved = ""
            if saved and saved not in boxes:
                boxes.append(saved)
            for text in [b.lower() for b in boxes] + [self.body_text()]:
                for word in self.SUCCESS_WORDS + self.ERROR_WORDS:
                    if word in text and word not in text_before:
                        return word, (boxes[0] if boxes else word)
            return None

        word, msg = WebDriverWait(
            self.driver,
            seconds,
            ignored_exceptions=(NoSuchElementException, StaleElementReferenceException),
        ).until(_new_message)
        try:
            self.driver.execute_script("sessionStorage.removeItem('__last_notify_msg');")
        except Exception:
            pass
        return word in self.SUCCESS_WORDS, msg

    def message_after(self, action) -> tuple[bool, str]:
        try:
            WebDriverWait(self.driver, 6).until(lambda _d: not self.visible(self.MESSAGE_BOX))
        except TimeoutException:
            pass
        try:
            self.driver.execute_script("""
                sessionStorage.removeItem('__last_notify_msg');
                if (typeof window.notify === 'function' && !window.__notify_wrapped) {
                    var orig = window.notify;
                    window.notify = function(title, message) {
                        var full = [title, message].filter(Boolean).join(' ').trim();
                        if (full) { sessionStorage.setItem('__last_notify_msg', full); }
                        return orig.apply(this, arguments);
                    };
                    window.__notify_wrapped = true;
                }
            """)
        except Exception:
            pass
        text_before = self.body_text()
        action()
        ok, message = self.wait_for_message(text_before)
        message = re.sub(r"^[×x]?\s*close\s*", "", " ".join(message.split()), flags=re.I)
        return ok, message

    def confirm(self, label: str = "yes", seconds: int = 15) -> bool:
        """Click the confirmation button in a SweetAlert or Bootstrap modal."""
        def _shown_button(d):
            for btn in d.find_elements(
                By.CSS_SELECTOR, ".swal2-confirm, .swal2-modal button, .modal.in button, .modal.show button"
            ):
                try:
                    if btn.is_displayed() and (
                        label in btn.text.lower() or "swal2-confirm" in (btn.get_attribute("class") or "")
                    ):
                        return btn
                except StaleElementReferenceException:
                    continue
            return None

        def _enabled_button(d):
            btn = _shown_button(d)
            try:
                if not (btn and btn.is_enabled() and "disabled" not in (btn.get_attribute("class") or "").lower()):
                    return None
                bars = [p for p in d.find_elements(By.ID, "progressBar") if p.is_displayed()]
                if bars and bars[0].get_attribute("value") != bars[0].get_attribute("max"):
                    return None
                return btn
            except StaleElementReferenceException:
                return None

        try:
            WebDriverWait(
                self.driver, min(seconds, 5), ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)
            ).until(_shown_button)
            btn = WebDriverWait(
                self.driver, seconds, ignored_exceptions=(NoSuchElementException, StaleElementReferenceException)
            ).until(_enabled_button)
            self.click(btn)
            return True
        except Exception:
            return False

    def confirm_any(self, labels: tuple[str, ...] = ("yes", "ok", "submit", "reject")) -> bool:
        for label in labels:
            if self.confirm(label, seconds=2):
                return True
        return False

    def do(self, label: str, confirm_label: str | None = None) -> tuple[bool, str]:
        def _action():
            self.click_label(label)
            if confirm_label:
                self.confirm(confirm_label)

        return self.message_after(_action)

    def do_near(self, anchor_text: str, label: str, confirm_label: str | None = None) -> tuple[bool, str]:
        def _action():
            self.click_near(anchor_text, label)
            if confirm_label:
                self.confirm(confirm_label)

        return self.message_after(_action)

    def alert_message(self, error=None) -> str:
        text = getattr(error, "alert_text", None) or ""
        if not text:
            try:
                alert = self.driver.switch_to.alert
                text = alert.text
                alert.accept()
            except NoAlertPresentException:
                pass
        return (text or "").strip()

    # ------------------------------------------------------------------
    # Forms, Select2, Bootstrap-Select & Downloads
    # ------------------------------------------------------------------

    def find_field(self, label_text: str):
        wanted = label_text.lower()
        labels = [lb for lb in self.driver.find_elements(By.TAG_NAME, "label") if lb.is_displayed()]
        for matches in (lambda t: t == wanted, lambda t: t.startswith(wanted), lambda t: wanted in t):
            for label in labels:
                if matches(self.clean(label.text)):
                    try:
                        return label.find_element(By.XPATH, self.FIELD_XPATH)
                    except NoSuchElementException:
                        continue
        return None

    def fill_field(self, label_text: str, value: str) -> None:
        field = WebDriverWait(self.driver, 10).until(lambda _d: self.find_field(label_text))
        field.clear()
        field.send_keys(value)

    def pick_option(self, label_text: str, option_text: str | None = None) -> str:
        field = WebDriverWait(self.driver, 10).until(lambda _d: self.find_field(label_text))
        if field.tag_name == "select" and field.is_displayed():
            select = Select(field)
            for option in select.options:
                if option.get_attribute("value") and (
                    not option_text or option_text.lower() in option.text.lower()
                ):
                    select.select_by_visible_text(option.text)
                    return option.text
            raise LookupError(f"No option '{option_text}' in '{label_text}'")

        button = field.find_element(
            By.XPATH, "following::*[contains(@class, 'dropdown-toggle') or contains(@class, 'select2-selection')][1]"
        )
        self.click(button)
        menu_css = ".dropdown-menu.open li:not(.disabled) a, .select2-results__option"
        options = WebDriverWait(self.driver, 5).until(
            lambda _d: [o for o in self.visible(menu_css) if o.text.strip()]
        )
        if option_text:
            options = [o for o in options if option_text.lower() in o.text.lower()] or options
        text = options[0].text
        self.click(options[0])
        return text

    def pick_bootstrap_select(
        self, data_id: str, option_text: str, root_xpath: str = "", timeout: int | None = None
    ) -> str:
        """Open a bootstrap-select dropdown by data-id and click the matching option."""
        waiter = WebDriverWait(self.driver, timeout) if timeout is not None else self.wait
        toggle = waiter.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[data-id='{data_id}']"))
        )
        self.click(toggle)
        opt_xpath = (
            f"{root_xpath}//button[@data-id='{data_id}']/following-sibling::div"
            f"//span[@class='text'][normalize-space()={self.xpath_text(option_text)}]"
        )
        option = waiter.until(EC.element_to_be_clickable((By.XPATH, opt_xpath)))
        chosen = option.text.strip()
        self.click(option)
        return chosen

    def select2_options(self, css: str) -> list:
        skip = ("please enter", "searching", "no result", "loading")
        try:
            return [
                o for o in self.driver.find_elements(By.CSS_SELECTOR, css)
                if o.is_displayed() and o.text.strip() and not any(w in o.text.lower() for w in skip)
            ]
        except StaleElementReferenceException:
            return []

    @staticmethod
    def best_option_index(options: list, term: str) -> int:
        wanted = term.strip().strip("/").lower()
        leaf = wanted.split("/")[-1]
        if "/" in wanted:
            for i, opt in enumerate(options):
                title = (opt.get_attribute("title") or opt.text or "").strip().strip("/").lower()
                if title == wanted or title.endswith(wanted):
                    return i
        for i, opt in enumerate(options):
            title = (opt.get_attribute("title") or opt.text or "").strip().strip("/").lower()
            if title == leaf or title.split("/")[-1] == leaf:
                return i
        return 0

    def pick_select2_by_id(self, select_id: str, term: str) -> None:
        box = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f"span.select2-selection[aria-labelledby='select2-{select_id}-container']")
            )
        )
        self.click(box)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input.select2-search__field")))
        wanted = term.strip().strip("/").split("/")[-1]
        for letter in wanted[:5]:
            ActionChains(self.driver).send_keys(letter).perform()
            time.sleep(0.15)

        option_css = f"#select2-{select_id}-results .select2-results__option"
        WebDriverWait(self.driver, 10).until(lambda _d: bool(self.select2_options(option_css)))
        self.wait_for_ajax_idle(timeout=5)

        def _chosen() -> bool:
            labels = self.driver.find_elements(By.ID, f"select2-{select_id}-container")
            if not labels:
                return True
            text = labels[0].text.replace("×", "").strip().lower()
            return bool(text) and "search for" not in text

        for _ in range(3):
            try:
                found = self.select2_options(option_css)
                target = found[self.best_option_index(found, term)]
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", target)
                ActionChains(self.driver).move_to_element(target).click().perform()
                break
            except (StaleElementReferenceException, IndexError):
                time.sleep(0.5)

        try:
            WebDriverWait(self.driver, 3).until(lambda _d: _chosen())
        except TimeoutException:
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            try:
                WebDriverWait(self.driver, 3).until(lambda _d: _chosen())
            except TimeoutException:
                pass
        if not _chosen():
            raise SetupError(f"the value '{wanted}' could not be selected in the '{select_id}' drop-down")

    def modal_text_input(self):
        boxes = self.driver.find_elements(By.XPATH, f"{self.MODAL}//input[@type='text' or not(@type)]")
        visible_boxes = [b for b in boxes if b.is_displayed() and b.is_enabled() and not b.get_attribute("readonly")]
        return visible_boxes[0] if visible_boxes else None

    def attach_to_file_input(self, path: str) -> None:
        modal_inputs = self.driver.find_elements(By.XPATH, f"{self.MODAL}//input[@type='file']")
        inputs = modal_inputs or [
            i for i in self.driver.find_elements(*self.FILE_INPUT)
            if i.get_attribute("id") != "signature_upload" and "swal2-file" not in (i.get_attribute("class") or "")
        ]
        file_input = inputs[-1]
        self.driver.execute_script(
            "arguments[0].style.display='block'; arguments[0].style.visibility='visible';",
            file_input,
        )
        file_input.send_keys(path)

    def form_problems(self) -> str:
        boxes = self.visible(".parsley-errors-list li, .parsley-custom-error-message, .validation-error-message")
        return " | ".join(box.text.strip() for box in boxes if box.text.strip())

    # ------------------------------------------------------------------
    # Tabs & Downloads
    # ------------------------------------------------------------------

    def switch_to_new_tab(self, old_tabs: list[str]) -> bool:
        if len(self.driver.window_handles) > len(old_tabs):
            self.driver.switch_to.window(self.driver.window_handles[-1])
            return True
        return False

    def close_extra_tabs(self, main_tab: str) -> None:
        for handle in list(self.driver.window_handles):
            if handle != main_tab:
                self.driver.switch_to.window(handle)
                self.driver.close()
        self.driver.switch_to.window(main_tab)

    def wait_for_download(
        self, before: set[str], seconds: int = 30, started: float | None = None
    ) -> str | None:
        """Wait for a finished file in cfg.DOWNLOAD_DIR (new, or overwritten since `started`)."""
        download_dir = str(cfg.DOWNLOAD_DIR)

        def _ready(_d):
            found = []
            for name in os.listdir(download_dir):
                if name.endswith((".crdownload", ".tmp")):
                    continue
                path = os.path.join(download_dir, name)
                if name not in before or (started is not None and os.path.getmtime(path) >= started - 1):
                    found.append((os.path.getmtime(path), name))
            if found:
                return max(found)[1]
            return False

        try:
            return WebDriverWait(self.driver, seconds, poll_frequency=0.5).until(_ready)
        except TimeoutException:
            return None
