"""Page Object for User Management: Users & User Approval Requests panels."""
from __future__ import annotations

import time
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from report.pages.base_page import BasePage


class UserManagementPage(BasePage):
    # Sidebar / Panel links
    USERS_PANEL_LINK = (
        By.XPATH,
        "//a[contains(@href, '/admin/user/list') or normalize-space(.)='Users']",
    )
    APPROVAL_PANEL_LINK = (
        By.XPATH,
        "//a[contains(@href, 'user-creation-requests') or contains(@href, 'approval') or contains(normalize-space(.), 'User Approval Request')]",
    )
    PAGE_HEADER = (By.CSS_SELECTOR, "h4.table_header, .table_header")

    # DataTable v1 controls (matches Robo2mation v6 DOM)
    TABLE_BODY_ROWS = (By.CSS_SELECTOR, "table.dataTable tbody tr")
    TABLE_HEADERS = (By.CSS_SELECTOR, ".dataTables_scrollHead thead th, table.dataTable thead th")
    TABLE_SEARCH_INPUT = (
        By.CSS_SELECTOR,
        "input.search_in_table, input[placeholder*='Type and press enter' i]",
    )
    COLUMN_TOGGLE_BTN = (
        By.CSS_SELECTOR,
        ".datatable-customize-columns-toggle-btn a, a[title='Toggle Columns']",
    )
    COLUMN_TOGGLE_ITEMS = (By.CSS_SELECTOR, ".data-table-column-toggle-list a.buttons-columnVisibility")
    DOWNLOAD_BTN = (
        By.CSS_SELECTOR,
        ".datatable-customize-download-btn a, a[title='Download']",
    )
    FILTER_TOGGLE_BTN = (By.CSS_SELECTOR, "#filterToggle a, #filterToggle, a[title='Filter']")
    FILTER_DRAWER = (By.CSS_SELECTOR, "#filterActionItems")

    # Action toolbar / modal controls
    ADD_USER_BTN = (
        By.CSS_SELECTOR,
        "#add_user_request_button, i[title='Add User Request'], "
        "a[title*='Add User' i], button[title*='Add User' i], #add_user_btn, a[href*='create']",
    )
    ACTION_BUTTONS_LOCATOR = (
        By.CSS_SELECTOR,
        ".datatable-top-items ul.actions a, .datatable-top-items ul.actions button, "
        ".activity-icons a, .activity-icons button, .dropdown-menu a, .dropdown-menu button, "
        ".action-bar a, .action-bar button, .selected-actions a, .selected-actions button, "
        "a[id$='_button'], button[id$='_button']",
    )
    TOAST_OR_ALERT = (
        By.CSS_SELECTOR,
        ".toast-message, .alert-success, .alert-info, .alert[data-notify='container'], "
        "[data-growl='container'], .growl-animated, .sweet-alert, .swal2-popup, .notify-msg",
    )

    # Add User / User Approval Request form controls
    FIRST_NAME_INPUT = (By.NAME, "first_name")
    LAST_NAME_INPUT = (By.NAME, "last_name")
    USERNAME_INPUT = (By.NAME, "username")
    EMAIL_INPUT = (By.NAME, "email")
    PASSWORD_INPUT = (By.ID, "password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "cfrm_password")
    COMMENT_INPUT = (By.ID, "comment")
    ROLE_SELECT = (By.ID, "role_select")
    ADD_USER_SUBMIT_BTN = (By.ID, "add_user_submit_button")
    POSITION_INPUT = (By.NAME, "position")
    EDIT_USER_BTN = (By.ID, "edit_button")
    EDIT_USER_SUBMIT_BTN = (By.ID, "edit_user_submit")

    def open(self, base_url: str, route: str) -> None:
        self.driver.get(f"{base_url.rstrip('/')}/{route.lstrip('/')}")
        self.wait_for_page_load()
        self.wait_for_ajax_idle()

    def assert_panels_visible(self) -> None:
        users_links = self.visible_elements(*self.USERS_PANEL_LINK)
        approval_links = self.visible_elements(*self.APPROVAL_PANEL_LINK)
        if not users_links or not approval_links:
            raise AssertionError(
                f"Expected both 'Users' and 'User Approval Requests' panels to be visible. "
                f"Found visible users={len(users_links)}, approval={len(approval_links)}."
            )

    def page_header_text(self, timeout: int = 10) -> str:
        def _visible_header(_d):
            for el in self.visible_elements(*self.PAGE_HEADER):
                text = el.text.strip()
                if text:
                    return text
            return False

        try:
            return WebDriverWait(self.driver, timeout).until(_visible_header)
        except TimeoutException:
            return ""

    def assert_page_header_contains(self, expected: str, timeout: int = 10) -> str:
        header = self.page_header_text(timeout=timeout)
        if expected.casefold() not in header.casefold():
            raise AssertionError(
                f"Expected page header containing '{expected}', but got '{header}' "
                f"(URL: {self.driver.current_url})."
            )
        return header

    def open_approval_requests_panel(self) -> None:
        links = self.visible_elements(*self.APPROVAL_PANEL_LINK)
        if not links:
            raise AssertionError("Visible 'User Approval Requests' panel link not found.")
        self.click(links[0])
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            lambda _d: any(
                "user approval request" in el.text.strip().casefold()
                for el in self.visible_elements(*self.PAGE_HEADER)
            )
        )
        self.wait_for_ajax_idle()

    def assert_table_has_rows(self, panel_name: str, timeout: int = 15) -> list:
        rows = self.visible_rows(timeout=timeout)
        if not rows:
            raise AssertionError(
                f"Expected '{panel_name}' table to display rows, but none loaded "
                f"(URL: {self.driver.current_url})."
            )
        return rows

    def visible_rows(self, timeout: int = 12):
        def _has_rows(_d):
            rows = [r for r in self.driver.find_elements(*self.TABLE_BODY_ROWS) if r.is_displayed()]
            return rows if rows else False

        try:
            return WebDriverWait(self.driver, timeout).until(_has_rows)
        except TimeoutException:
            return []

    def dismiss_growl_notifications(self) -> None:
        for close_btn in self.visible_elements(
            By.CSS_SELECTOR,
            "[data-growl='container'] .close, [data-growl='container'] [data-growl='dismiss'], "
            ".growl-animated .close",
        ):
            try:
                self.click(close_btn)
            except Exception:
                pass
        try:
            WebDriverWait(self.driver, 5).until(
                lambda _d: not self.visible_elements(
                    By.CSS_SELECTOR, "[data-growl='container'], .growl-animated"
                )
            )
        except TimeoutException:
            pass

    def search_table(self, query: str) -> None:
        self.dismiss_growl_notifications()
        search_box = self.wait.until(EC.visibility_of_element_located(self.TABLE_SEARCH_INPUT))
        self.set_value(search_box, query)
        search_box.send_keys(Keys.ENTER)
        self.wait_for_ajax_idle()
        time.sleep(0.5)

    def sort_first_sortable_column(self) -> str:
        headers = [
            h for h in self.driver.find_elements(*self.TABLE_HEADERS)
            if h.is_displayed() and h.text.strip() and "sorting" in (h.get_attribute("class") or "")
        ]
        if not headers:
            raise LookupError("No sortable column headers found in the table.")
        target = headers[0]
        label = target.text.strip()
        self.click(target)
        self.wait_for_ajax_idle()
        return label

    def test_column_toggle(self) -> None:
        toggle = self.wait.until(EC.element_to_be_clickable(self.COLUMN_TOGGLE_BTN))
        self.click(toggle)
        time.sleep(0.3)
        items = [i for i in self.driver.find_elements(*self.COLUMN_TOGGLE_ITEMS) if i.is_displayed()]
        if not items:
            raise LookupError("Column toggle menu opened, but no column visibility items were found.")
        # Toggle off and back on to verify without leaving UI altered
        self.click(items[-1])
        time.sleep(0.3)
        self.click(items[-1])
        time.sleep(0.3)
        self.click(toggle)

    def open_filter_drawer(self) -> None:
        toggles = self.visible_elements(*self.FILTER_TOGGLE_BTN)
        if not toggles:
            raise LookupError("Filter toggle button (#filterToggle) was not found.")
        drawer = self.driver.find_elements(*self.FILTER_DRAWER)
        if not drawer or "close" in (drawer[0].get_attribute("class") or ""):
            self.click(toggles[0])
            time.sleep(0.4)

    def download_export(self, action: str, download_folder: Path, timeout: int = 20) -> Path | None:
        before = {p.name for p in download_folder.glob("*") if p.is_file()}
        trigger = self.wait.until(EC.element_to_be_clickable(self.DOWNLOAD_BTN))
        self.click(trigger)
        time.sleep(0.4)

        key = action.casefold()
        btn = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f".data-table-btn-list .buttons-{key}"))
        )
        self.click(btn)
        time.sleep(0.6)

        if key == "copy":
            return None

        deadline = time.time() + timeout
        while time.time() < deadline:
            if not list(download_folder.glob("*.crdownload")):
                new_files = [
                    p for p in download_folder.glob("*")
                    if p.is_file() and p.name not in before
                ]
                if new_files:
                    return new_files[0]
            time.sleep(0.5)
        raise TimeoutError(f"Expected '{action}' export file was not downloaded within {timeout}s.")

    def select_row_by_text(self, match_text: str = "") -> None:
        rows = self.visible_rows()
        if not rows:
            raise AssertionError("No visible rows found to select.")
        target_row = rows[0]
        if match_text:
            matched = next((r for r in rows if match_text.casefold() in r.text.casefold()), None)
            if matched is None:
                raise LookupError(f"Row containing '{match_text}' was not found in the table.")
            target_row = matched

        checkboxes = target_row.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        if checkboxes:
            self.click(checkboxes[0])
        else:
            cells = target_row.find_elements(By.TAG_NAME, "td")
            self.click(cells[0] if cells else target_row)
        time.sleep(0.4)

    @staticmethod
    def _element_action_label(el) -> str:
        label = (
            el.get_attribute("title")
            or el.get_attribute("data-original-title")
            or ""
        ).strip()
        if not label:
            for icon in el.find_elements(By.TAG_NAME, "i"):
                icon_label = (
                    icon.get_attribute("title")
                    or icon.get_attribute("data-original-title")
                    or ""
                ).strip()
                if icon_label:
                    label = icon_label
                    break
        return label or (el.text or "").strip()

    def visible_row_action_labels(self) -> list[str]:
        labels: list[str] = []
        seen: set[str] = set()
        for el in self.driver.find_elements(*self.ACTION_BUTTONS_LOCATOR):
            try:
                if not el.is_displayed():
                    continue
                label = self._element_action_label(el)
                if label and label not in seen:
                    seen.add(label)
                    labels.append(label)
            except Exception:
                continue
        return labels

    def assert_row_actions_present(self, expected_actions: list[str]) -> list[str]:
        available = self.visible_row_action_labels()
        norm_avail = [a.casefold() for a in available]
        missing = [
            req for req in expected_actions
            if not any(req.casefold() in a for a in norm_avail)
        ]
        if missing:
            raise AssertionError(
                f"Missing expected row actions: {missing}. Visible actions: {available}"
            )
        return available

    def click_row_action(self, action_name: str) -> None:
        wanted = action_name.casefold()
        for el in self.driver.find_elements(*self.ACTION_BUTTONS_LOCATOR):
            if not el.is_displayed():
                continue
            label = self._element_action_label(el).casefold()
            text = (el.text or "").strip().casefold()
            if wanted in label or wanted in text:
                self.click(el)
                time.sleep(0.4)
                return
        raise LookupError(f"Row action '{action_name}' was not found.")

    def submit_reject_with_comment(self, comment: str) -> str:
        # Verify comment is mandatory before filling (CON-TC016 note)
        confirm_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".modal.in button[type='submit'], .modal.show button.btn-danger, button#reject_btn")
            )
        )
        comment_box = self.wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, ".modal.in textarea, .modal.show textarea, textarea[name*='comment' i]")
            )
        )
        self.set_value(comment_box, comment)
        self.click(confirm_btn)
        self.wait_for_ajax_idle()
        return self.read_confirmation_message()

    def read_confirmation_message(self) -> str:
        try:
            el = WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(self.TOAST_OR_ALERT)
            )
            return el.text.strip()
        except TimeoutException:
            return ""

    def open_add_user_request_form(self) -> None:
        btn = self.wait.until(EC.visibility_of_element_located(self.ADD_USER_BTN))
        self.click(btn)
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(self.FIRST_NAME_INPUT)
        )
        self.wait_for_ajax_idle()

    def select_first_available_role(self) -> str:
        select_el = self.wait.until(EC.presence_of_element_located(self.ROLE_SELECT))
        options = [
            (opt.get_attribute("value") or "", opt.text.strip())
            for opt in select_el.find_elements(By.TAG_NAME, "option")
        ]
        target = next(
            (
                (val, label)
                for val, label in options
                if val.strip() and "nothing selected" not in label.casefold()
            ),
            None,
        )
        if not target:
            raise LookupError("No selectable roles found in #role_select.")
        target_val, target_label = target

        # Try clicking via Bootstrap selectpicker toggle first
        toggle_btns = self.driver.find_elements(By.CSS_SELECTOR, "button[data-id='role_select']")
        if not toggle_btns:
            toggle_btns = select_el.find_elements(
                By.XPATH,
                "./ancestor::div[contains(@class,'bootstrap-select')][1]//button[contains(@class,'dropdown-toggle')]",
            )
        if toggle_btns and toggle_btns[0].is_displayed():
            self.click(toggle_btns[0])
            time.sleep(0.3)
            menu_items = [
                el
                for el in self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".bootstrap-select.open .dropdown-menu li a, .dropdown-menu.open li a, .dropdown-menu.show li a",
                )
                if el.is_displayed() and target_label.casefold() in el.text.strip().casefold()
            ]
            if menu_items:
                self.click(menu_items[0])
                time.sleep(0.3)

        current_val = (select_el.get_attribute("value") or "").strip()
        if current_val != target_val:
            self.driver.execute_script(
                "var el = arguments[0], val = arguments[1];"
                "if (window.jQuery && window.jQuery(el).selectpicker) {"
                "  window.jQuery(el).selectpicker('val', val).trigger('change');"
                "} else {"
                "  el.value = val;"
                "  el.dispatchEvent(new Event('change', {bubbles: true}));"
                "}",
                select_el,
                target_val,
            )
            time.sleep(0.3)

        final_val = (select_el.get_attribute("value") or "").strip()
        if not final_val:
            raise AssertionError(f"Failed to select role '{target_label}' in #role_select.")
        return target_label

    def fill_and_submit_user_request(
        self,
        *,
        first_name: str,
        last_name: str,
        username: str,
        email: str,
        password: str,
        comment: str = "",
    ) -> tuple[str, str]:
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.FIRST_NAME_INPUT)), first_name)
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.LAST_NAME_INPUT)), last_name)
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT)), username)
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.EMAIL_INPUT)), email)
        selected_role = self.select_first_available_role()
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT)), password)
        self.set_value(self.wait.until(EC.visibility_of_element_located(self.CONFIRM_PASSWORD_INPUT)), password)
        if comment:
            self.set_value(self.wait.until(EC.visibility_of_element_located(self.COMMENT_INPUT)), comment)

        submit_btn = self.wait.until(EC.element_to_be_clickable(self.ADD_USER_SUBMIT_BTN))
        self.click(submit_btn)
        confirm_msg = self._wait_for_submission_confirmation("add_user", "User approval request submission")
        return confirm_msg, selected_role

    def _wait_for_submission_confirmation(self, form_url_fragment: str, action_label: str) -> str:
        """Poll for a visible confirmation toast/modal after submitting a user management form."""
        confirm_msg = ""
        deadline = time.time() + 15
        while time.time() < deadline:
            for el in self.visible_elements(*self.TOAST_OR_ALERT):
                try:
                    text = " ".join(el.text.split())
                except Exception:
                    continue
                if text:
                    confirm_msg = text
                    break

            for ok_btn in self.visible_elements(By.CSS_SELECTOR, ".swal2-confirm, .sweet-alert button.confirm"):
                try:
                    self.click(ok_btn)
                    time.sleep(0.3)
                except Exception:
                    pass

            if confirm_msg and form_url_fragment not in self.driver.current_url.casefold():
                break
            time.sleep(0.2)

        if not confirm_msg and form_url_fragment in self.driver.current_url.casefold():
            errors = [
                el.text.strip()
                for el in self.visible_elements(
                    By.CSS_SELECTOR,
                    ".alert-danger, .toast-error, .text-danger, .help-block, .errorlist, .invalid-feedback",
                )
                if el.text.strip()
            ]
            raise AssertionError(
                f"{action_label} did not produce a confirmation message. "
                f"Errors: {errors or ['none']} (URL: {self.driver.current_url})."
            )

        self.wait_for_page_load()
        self.wait_for_ajax_idle()
        return confirm_msg

    def _open_edit_form_from_selected_row(self) -> None:
        edit_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.EDIT_USER_BTN)
        )
        self.click(edit_btn)
        self.wait_for_page_load()
        WebDriverWait(self.driver, 15).until(
            lambda d: "edit_user" in d.current_url.casefold()
            and self.visible_elements(*self.FIRST_NAME_INPUT)
        )
        self.wait_for_ajax_idle()

    def open_edit_user_request_form(self, match_text: str) -> None:
        """Select a request row by text and open its Edit User Request form."""
        self.dismiss_growl_notifications()
        self.select_row_by_text(match_text)
        self._open_edit_form_from_selected_row()

    def edit_selected_user_and_submit(self) -> str:
        """Open Edit User Request for the already-selected row, update fields, and submit."""
        self._open_edit_form_from_selected_row()
        ts = time.strftime("%m%d%H%M%S")
        confirm_msg = self.update_and_submit_user_request(
            position=f"QA Updated {ts}",
            comment=f"Updated before approval ({ts})",
        )
        if not confirm_msg:
            raise AssertionError("Expected a confirmation message after submitting user update request.")
        return confirm_msg

    def assert_activity_logged(self, base_url: str, route: str, expected_keywords: list[str]) -> str:
        """Open the activity report and verify a visible row matches all expected keywords."""
        self.open(base_url, route)
        keywords = [k.strip().casefold() for k in expected_keywords if k and k.strip()]
        rows = self.visible_rows(timeout=12)
        for row in rows:
            try:
                text = row.text.strip()
            except Exception:
                continue
            text_cf = text.casefold()
            if all(kw in text_cf for kw in keywords):
                return " ".join(text.split())[:140]

        top_rows = [r.text.strip() for r in rows[:3]]
        raise AssertionError(
            f"Expected activity row matching {expected_keywords}, but none matched. "
            f"Top visible rows: {top_rows}"
        )

    def update_and_submit_user_request(
        self,
        *,
        last_name: str = "",
        position: str = "",
        comment: str = "",
    ) -> str:
        """Update editable fields on Edit User Request and submit."""
        if last_name:
            self.set_value(self.wait.until(EC.visibility_of_element_located(self.LAST_NAME_INPUT)), last_name)
        if position:
            self.set_value(self.wait.until(EC.visibility_of_element_located(self.POSITION_INPUT)), position)
        if comment:
            self.set_value(self.wait.until(EC.visibility_of_element_located(self.COMMENT_INPUT)), comment)

        submit_btn = self.wait.until(EC.element_to_be_clickable(self.EDIT_USER_SUBMIT_BTN))
        self.click(submit_btn)
        return self._wait_for_submission_confirmation("edit_user", "User update request submission")

    def find_row_containing(self, needle: str, timeout: int = 12) -> str:
        wanted = needle.casefold()
        for row in self.visible_rows(timeout=timeout):
            try:
                text = row.text.strip()
            except Exception:
                continue
            if wanted in text.casefold():
                return text
        return ""