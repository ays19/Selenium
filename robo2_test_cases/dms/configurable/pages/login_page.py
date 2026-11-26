"""Page Object for Robo2mation Login, Account Lockout, Status Errors, and Microsoft SSO."""
from __future__ import annotations

import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from report.pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = (
        By.XPATH,
        "//input[contains(@placeholder, 'Username') or @name='username' or @id='username']",
    )
    PASSWORD_INPUT = (
        By.XPATH,
        "//input[contains(@placeholder, 'Password') or @name='password' or @id='password']",
    )
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit'], button.btn-login, input[type='submit']")
    ERROR_CONTAINER = (
        By.CSS_SELECTOR,
        ".alert-danger, .alert-warning, .alert, [data-growl='container'], .growl-animated, "
        ".errorlist, .toast-error, .sweet-alert, .swal2-popup, .help-block, .text-danger, .login-error",
    )
    MICROSOFT_LOGIN_BTN = (
        By.XPATH,
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'microsoft')] "
        "| //button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'microsoft')]",
    )
    LOGOUT_LINK = (By.CSS_SELECTOR, "a[href*='logout']")

    def clear_session(self) -> None:
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script(
                "window.localStorage.clear(); window.sessionStorage.clear();"
            )
        except Exception:
            pass

    def is_login_page_displayed(self, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.USERNAME_INPUT)
            )
            return True
        except TimeoutException:
            return False

    def open_login(self, base_url: str) -> None:
        base = base_url.rstrip("/")
        self.driver.get(base)
        self.wait_for_page_load()
        if not self.is_login_page_displayed(timeout=4):
            self.clear_session()
            self.driver.get(f"{base}/login/")
            self.wait_for_page_load()

    def logout_if_needed(self, base_url: str) -> None:
        base = base_url.rstrip("/")
        self.driver.get(f"{base}/login/logout/")
        self.wait_for_page_load()
        if not self.is_login_page_displayed(timeout=4):
            self.clear_session()

    def submit_credentials(self, username: str, password: str) -> None:
        user_el = self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT))
        user_el.clear()
        user_el.send_keys(username)

        pass_el = self.wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))
        pass_el.clear()
        pass_el.send_keys(password, Keys.ENTER)
        self.wait_for_page_load()
        time.sleep(0.5)

    def login_expect_success(self, base_url: str, username: str, password: str) -> None:
        self.open_login(base_url)
        self.submit_credentials(username, password)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.invisibility_of_element_located(self.USERNAME_INPUT)
            )
        except TimeoutException as exc:
            raise AssertionError(
                f"Login as '{username}' failed (still on login page: {self.driver.current_url}). "
                f"Page message: {self.read_error_text()[:250]}"
            ) from exc

    def login_expect_error(
        self, base_url: str, username: str, password: str, expected_substring: str
    ) -> str:
        self.open_login(base_url)
        self.submit_credentials(username, password)
        last_error = ""
        deadline = time.time() + 12
        while time.time() < deadline:
            texts = [
                " ".join(el.text.split())
                for el in self.visible_elements(*self.ERROR_CONTAINER)
                if el.text.strip()
            ]
            combined = " | ".join(texts)
            if combined:
                if len(combined) >= len(last_error):
                    last_error = combined
                if expected_substring.casefold() in combined.casefold():
                    return combined
            time.sleep(0.25)

        error_text = last_error or self.read_error_text()
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