"""Reusable Selenium BasePage with explicit-wait UI helpers."""
from __future__ import annotations

import re

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait


class BasePage:
    """Base Page Object providing explicit-wait Selenium primitives."""

    BODY_LOCATOR = (By.TAG_NAME, "body")
    FIELD_CANDIDATES_LOCATOR = (
        By.CSS_SELECTOR,
        "input:not([type='hidden']), textarea, select, [role='combobox']",
    )
    LABEL_ELEMENTS_LOCATOR = (By.XPATH, "//label")
    ACTION_BUTTONS_LOCATOR = (
        By.CSS_SELECTOR,
        "button, input[type='submit'], input[type='button'], a.btn, button.btn",
    )
    LOADING_INDICATORS_LOCATOR = (
        By.CSS_SELECTOR,
        ".dataTables_processing, .ant-spin-spinning, .loading-spinner",
    )

    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    @staticmethod
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()

    def wait_for_page_load(self) -> None:
        """Wait until document.readyState == 'complete'."""
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def wait_for_ajax_idle(self, timeout: int = 15) -> None:
        """Wait until visible spinners, DataTables loaders, and jQuery AJAX calls finish."""
        def _is_idle(driver) -> bool:
            if self.visible_elements(*self.LOADING_INDICATORS_LOCATOR):
                return False
            return bool(
                driver.execute_script(
                    "var els = document.querySelectorAll('[style*=\"--datatable-loading-index\"]');"
                    "for (var i = 0; i < els.length; i++) {"
                    "  var v = parseInt(els[i].style.getPropertyValue('--datatable-loading-index'), 10);"
                    "  if (!isNaN(v) && v > 0) return false;"
                    "}"
                    "return !window.jQuery || window.jQuery.active === 0;"
                )
            )

        try:
            WebDriverWait(self.driver, timeout).until(_is_idle)
        except TimeoutException:
            pass

    def body_text(self) -> str:
        try:
            return self.driver.find_element(*self.BODY_LOCATOR).text
        except StaleElementReferenceException:
            return self.driver.find_element(*self.BODY_LOCATOR).text

    def visible_elements(self, by: By, selector: str):
        found = []
        for element in self.driver.find_elements(by, selector):
            try:
                if element.is_displayed():
                    found.append(element)
            except StaleElementReferenceException:
                continue
        return found

    def click(self, element) -> None:
        self.wait.until(lambda _driver: element.is_displayed() and element.is_enabled())
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        try:
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException) as exc:
            raise RuntimeError(
                "Target control is visible but cannot be clicked (check overlays or modal state)."
            ) from exc

    def set_value(self, element, value: str) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        if element.tag_name.lower() == "select":
            Select(element).select_by_visible_text(value)
            return
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(value)

    def find_labeled_field(self, label_text: str):
        wanted = self.normalize(label_text)
        ranked = []

        for element in self.driver.find_elements(*self.FIELD_CANDIDATES_LOCATOR):
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                attrs = (
                    element.get_attribute("placeholder"),
                    element.get_attribute("name"),
                    element.get_attribute("id"),
                    element.get_attribute("aria-label"),
                    element.get_attribute("title"),
                )
                descriptor = self.normalize(" ".join(v or "" for v in attrs))
                score = 4 if descriptor == wanted else (3 if wanted and wanted in descriptor else 0)

                if not score:
                    element_id = element.get_attribute("id")
                    if element_id:
                        labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{element_id}']")
                        label_words = self.normalize(" ".join(lbl.text for lbl in labels))
                        score = 4 if label_words == wanted else (3 if wanted and wanted in label_words else 0)

                if score:
                    ranked.append((score, element))
            except StaleElementReferenceException:
                continue

        if ranked:
            ranked.sort(key=lambda item: item[0], reverse=True)
            return ranked[0][1]

        # Fallback for label + following input layouts
        for label in self.driver.find_elements(*self.LABEL_ELEMENTS_LOCATOR):
            if wanted and wanted in self.normalize(label.text):
                label_for = label.get_attribute("for")
                if label_for:
                    matches = self.driver.find_elements(By.ID, label_for)
                    if matches:
                        return matches[0]
                following = label.find_elements(
                    By.XPATH,
                    "following::input[1] | following::select[1] | following::textarea[1]",
                )
                if following:
                    return following[0]

        raise LookupError(f"Could not locate a visible field labelled '{label_text}'.")

    def apply_form(self, fallback_field=None) -> None:
        action_words = {"search", "filter", "apply", "show", "submit", "generate"}
        for button in self.driver.find_elements(*self.ACTION_BUTTONS_LOCATOR):
            try:
                label = self.normalize(
                    button.text
                    or button.get_attribute("value")
                    or button.get_attribute("aria-label")
                    or ""
                )
                if (
                    button.is_displayed()
                    and button.is_enabled()
                    and any(word == label or word in label.split() for word in action_words)
                ):
                    self.click(button)
                    return
            except StaleElementReferenceException:
                continue

        if fallback_field is not None:
            fallback_field.send_keys(Keys.ENTER)
            return
        raise LookupError("No visible Search/Filter/Apply button was found on the page.")
