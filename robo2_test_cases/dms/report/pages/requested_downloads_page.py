"""Page Object for the application's Requested Downloads screen."""
from __future__ import annotations

from selenium.webdriver.common.by import By
from .base_page import BasePage


class RequestedDownloadsPage(BasePage):
    """Page Object for the Requested Downloads queue screen."""

    TABLE_ROWS_LOCATOR = (By.CSS_SELECTOR, "table tbody tr")
    LINKS_LOCATOR = (By.CSS_SELECTOR, "a[href]")

    def open(self, url: str) -> None:
        self.driver.get(url)
        self.wait_for_page_load()

    def assert_download_request_visible(self, expected_text: str = "") -> None:
        body = self.body_text().casefold()
        tables = self.driver.find_elements(*self.TABLE_ROWS_LOCATOR)
        links = self.driver.find_elements(*self.LINKS_LOCATOR)
        has_download_link = any(
            link.is_displayed() and (
                "download" in (link.text or "").casefold()
                or "download" in (link.get_attribute("href") or "").casefold()
            ) for link in links
        )
        if expected_text:
            if expected_text.casefold() not in body:
                raise AssertionError(f"Requested Downloads did not show expected entry '{expected_text}'.")
            return
        if not tables and not has_download_link:
            raise AssertionError("No requested-download table or download link was visible.")
