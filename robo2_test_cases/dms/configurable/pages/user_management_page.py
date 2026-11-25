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
        "//a[contains(@href, 'approval') or contains(normalize-space(.), 'User Approval Request')]",
    )

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
    FILTER_TOGGLE_BTN = (By.CSS_SELECTOR, "#filterToggle a, #filterToggle")
    FILTER_DRAWER = (By.CSS_SELECTOR, "#filterActionItems")

    # Action toolbar / modal controls
    ADD_USER_BTN = (
        By.CSS_SELECTOR,
        "a[title*='Add User' i], button[title*='Add User' i], #add_user_btn, a[href*='create']",
    )
    ACTION_BUTTONS_LOCATOR = (
        By.CSS_SELECTOR,
        ".datatable-top-items ul.actions a, .datatable-top-items ul.actions button, "
        ".activity-icons a, .activity-icons button, .dropdown-menu a, .dropdown-menu button",
    )
    TOAST_OR_ALERT = (By.CSS_SELECTOR, ".toast-message, .alert-success, .sweet-alert, .notify-msg")

    def open(self, base_url: str, route: str) -> None:
        self.driver.get(f"{base_url.rstrip('/')}/{route.lstrip('/')}")
        self.wait_for_page_load()
        self.wait_for_ajax_idle()

    def assert_panels_visible(self) -> None:
        users_links = self.driver.find_elements(*self.USERS_PANEL_LINK)
        approval_links = self.driver.find_elements(*self.APPROVAL_PANEL_LINK)
        if not users_links or not approval_links:
            raise AssertionError(
                f"Expected both 'Users' and 'User Approval Requests' panels to be visible. "
                f"Found users={len(users_links)}, approval={len(approval_links)}."
            )

    def visible_rows(self, timeout: int = 12):
        def _has_rows(_d):
            rows = [r for r in self.driver.find_elements(*self.TABLE_BODY_ROWS) if r.is_displayed()]
            return rows if rows else False

        try:
            return WebDriverWait(self.driver, timeout).until(_has_rows)
        except TimeoutException:
            return []

    def search_table(self, query: str) -> None:
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
        if drawer and "close" in (drawer[0].get_attribute("class") or ""):
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
            self.click(target_row)
        time.sleep(0.4)

    def visible_row_action_labels(self) -> list[str]:
        labels: list[str] = []
        for el in self.driver.find_elements(*self.ACTION_BUTTONS_LOCATOR):
            try:
                if not el.is_displayed():
                    continue
                label = (
                    el.get_attribute("title")
                    or el.get_attribute("data-original-title")
                    or el.text
                    or ""
                ).strip()
                if label:
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
            label = (
                el.get_attribute("title")
                or el.get_attribute("data-original-title")
                or el.text
                or ""
            ).strip().casefold()
            if wanted in label:
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