"""Page Object for Robo2mation Login, Account Lockout, Status Errors, and Microsoft SSO."""
from __future__ import annotations

import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from report.pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[name='username'], input#username, input[type='text']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password'], input#password, input[type='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], button.btn-login, input[type='submit']")
    ERROR_CONTAINER = (
        By.CSS_SELECTOR,
        ".alert-danger, .errorlist, .toast-error, .sweet-alert, .help-block, .text-danger, .login-error",
    )
    MICROSOFT_LOGIN_BTN = (
        By.XPATH,
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'microsoft')] "
        "| //button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'microsoft')]",
    )
    LOGOUT_LINK = (By.CSS_SELECTOR, "a[href*='logout']")

    def open_login(self, base_url: str) -> None:
        self.driver.get(f"{base_url.rstrip('/')}/login/")
        self.wait_for_page_load()

    def logout_if_needed(self, base_url: str) -> None:
        self.driver.get(f"{base_url.rstrip('/')}/login/logout/")
        self.wait_for_page_load()

    def submit_credentials(self, username: str, password: str) -> None:
        user_el = self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT))
        pass_el = self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))
        self.set_value(user_el, username)
        self.set_value(pass_el, password)
        btn = self.wait.until(EC.element_to_be_clickable(self.LOGIN_BUTTON))
        self.click(btn)
        self.wait_for_page_load()
        time.sleep(0.6)

    def login_expect_success(self, base_url: str, username: str, password: str) -> None:
        self.open_login(base_url)
        self.submit_credentials(username, password)
        WebDriverWait(self.driver, 15).until(
            lambda d: "/login" not in d.current_url.casefold() or "dashboard" in d.current_url.casefold()
        )

    def login_expect_error(
        self, base_url: str, username: str, password: str, expected_substring: str
    ) -> str:
        self.open_login(base_url)
        self.submit_credentials(username, password)
        error_text = self.read_error_text()
        if expected_substring.casefold() not in error_text.casefold():
            raise AssertionError(
                f"Expected login error containing '{expected_substring}', "
                f"but got: '{error_text[:300]}' (URL: {self.driver.current_url})"
            )
        return error_text

    def read_error_text(self) -> str:
        texts = [
            el.text.strip()
            for el in self.visible_elements(*self.ERROR_CONTAINER)
            if el.text.strip()
        ]
        return " | ".join(texts) if texts else self.body_text()

    def trigger_lockout(self, base_url: str, username: str, attempts: int = 5) -> str:
        last_msg = ""
        for i in range(1, attempts + 1):
            self.open_login(base_url)
            self.submit_credentials(username, f"WrongPass!{i}99")
            last_msg = self.read_error_text()
        return last_msg

    def login_with_microsoft(self, base_url: str, email: str, password: str) -> None:
        self.open_login(base_url)
        ms_btn = self.wait.until(EC.element_to_be_clickable(self.MICROSOFT_LOGIN_BTN))
        self.click(ms_btn)

        # Handle Microsoft Identity Platform OAuth flow
        email_input = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "loginfmt"))
        )
        self.set_value(email_input, email)
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))))

        pwd_input = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.NAME, "passwd"))
        )
        self.set_value(pwd_input, password)
        self.click(self.wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))))

        # Optional "Stay signed in?" prompt
        try:
            stay_btn = WebDriverWait(self.driver, 6).until(
                EC.element_to_be_clickable((By.ID, "idSIButton9"))
            )
            self.click(stay_btn)
        except TimeoutException:
            pass

        WebDriverWait(self.driver, 25).until(
            lambda d: "dashboard" in d.current_url.casefold()
        )