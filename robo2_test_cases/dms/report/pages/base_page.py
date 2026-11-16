"""Reusable Selenium page-object primitives for Report pages."""
from __future__ import annotations

import re
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class BasePage:
    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    @staticmethod
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()

    def body_text(self) -> str:
        try:
            return self.driver.find_element(By.TAG_NAME, "body").text
        except StaleElementReferenceException:
            return self.driver.find_element(By.TAG_NAME, "body").text

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
                "The target control is visible but cannot be clicked. Check overlays, modal state, or the locator."
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
        candidates = self.driver.find_elements(
            By.CSS_SELECTOR,
            "input:not([type='hidden']), textarea, select, [role='combobox']",
        )
        ranked = []
        for element in candidates:
            try:
                if not element.is_displayed() or not element.is_enabled():
                    continue
                attrs = [
                    element.get_attribute("placeholder"), element.get_attribute("name"),
                    element.get_attribute("id"), element.get_attribute("aria-label"),
                    element.get_attribute("title"),
                ]
                descriptor = self.normalize(" ".join(value or "" for value in attrs))
                score = 0
                if descriptor == wanted:
                    score = 4
                elif wanted and wanted in descriptor:
                    score = 3
                else:
                    element_id = element.get_attribute("id")
                    if element_id:
                        labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{element_id}']")
                        label_words = self.normalize(" ".join(label.text for label in labels))
                        if label_words == wanted:
                            score = 4
                        elif wanted and wanted in label_words:
                            score = 3
                if score:
                    ranked.append((score, element))
            except StaleElementReferenceException:
                continue
        if ranked:
            ranked.sort(key=lambda item: item[0], reverse=True)
            return ranked[0][1]

        # Fallback for common label + following input layouts.
        labels = self.driver.find_elements(By.XPATH, "//label")
        for label in labels:
            if wanted and wanted in self.normalize(label.text):
                label_for = label.get_attribute("for")
                if label_for:
                    matches = self.driver.find_elements(By.ID, label_for)
                    if matches:
                        return matches[0]
                following = label.find_elements(By.XPATH, "following::input[1] | following::select[1] | following::textarea[1]")
                if following:
                    return following[0]
        raise LookupError(f"Could not locate a visible field labelled '{label_text}'. Configure the field selector for this report.")

    def apply_form(self, fallback_field=None) -> None:
        action_words = {"search", "filter", "apply", "show", "submit", "generate"}
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR,
            "button, input[type='submit'], input[type='button'], a.btn, button.btn",
        )
        for button in buttons:
            try:
                label = self.normalize(button.text or button.get_attribute("value") or button.get_attribute("aria-label") or "")
                if button.is_displayed() and button.is_enabled() and any(word == label or word in label.split() for word in action_words):
                    self.click(button)
                    return
            except StaleElementReferenceException:
                continue
        if fallback_field is not None:
            fallback_field.send_keys(Keys.ENTER)
            return
        raise LookupError("No visible Search/Filter/Apply button was found on the report page.")
