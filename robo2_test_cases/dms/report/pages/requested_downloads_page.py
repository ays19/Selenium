"""Page Object for the Robo2mation Requested Downloads queue screen."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from .base_page import BasePage


class RequestedDownloadsPage(BasePage):
    """Verifies queued report exports on the Requested Downloads screen."""

    TABLE_ROWS_LOCATOR = (By.CSS_SELECTOR, "table tbody tr")
    LINKS_LOCATOR = (By.CSS_SELECTOR, "a[href]")

    def open(self, url: str) -> None:
        self.driver.get(url)
        self.wait_for_page_load()
        self.wait_for_ajax_idle()

    def assert_download_request_visible(self, expected_text: str = "") -> None:
        body = self.body_text().casefold()
        if expected_text:
            if expected_text.casefold() not in body:
                raise AssertionError(
                    f"Requested Downloads did not show expected entry '{expected_text}'."
                )
            return

        rows = [
            r for r in self.driver.find_elements(*self.TABLE_ROWS_LOCATOR)
            if "no data" not in (r.text or "").casefold()
        ]
        has_download_link = any(
            link.is_displayed()
            and (
                "download" in (link.text or "").casefold()
                or "download" in (link.get_attribute("href") or "").casefold()
            )
            for link in self.driver.find_elements(*self.LINKS_LOCATOR)
        )
        if not rows and not has_download_link:
            raise AssertionError(
                "No requested-download table row or download link was visible."
            )
