"""Page Object for DMS Pending For Review (Maker-Checker) workflow."""
from __future__ import annotations

import dms_config as cfg

from .base_page import BasePage


class ReviewPage(BasePage):
    """Encapsulates Pending For Review actions and Requested By Me / Checker filters."""

    def open(self) -> None:
        self.driver.get(cfg.REVIEW_URL)
        self.wait_for_page_load()
        self.wait_for_ajax_idle(timeout=6)

    def review_document(self, name: str, action: str) -> tuple[bool, str]:
        """Open Pending For Review and approve/reject `name` as the current logged-in user."""
        self.open()
        if not self.wait_text(name, 10):
            return False, "document not listed for the checker"

        def _click_action():
            self.click_near(name, action)
            box = self.modal_text_input()
            if box is not None:
                box.send_keys("AUTO review")
            self.confirm_any()

        return self.message_after(_click_action)

    def has_checker_actions(self, name: str) -> tuple[bool, bool, bool]:
        """Open Pending For Review ('Requested by others' default) and check approve/reject availability."""
        self.open()
        shown = self.wait_text(name, 10)
        approve = self.find_near(name, "approve") is not None
        reject = self.find_near(name, "reject") is not None
        return shown, approve, reject

    def is_listed_in_requested_by_me(self, status: str, name: str) -> bool:
        self.open()
        self.pick_bootstrap_select("select-user", "Requested By Me")
        self.wait_for_ajax_idle(timeout=5)
        self.pick_bootstrap_select("select-status", status)
        self.wait_for_ajax_idle(timeout=6)
        return name.lower() in self.body_text()

    def requested_by_me_statuses(self, name: str) -> list[bool]:
        return [
            self.is_listed_in_requested_by_me(status, name)
            for status in ("Pending", "Approved", "Rejected")
        ]
