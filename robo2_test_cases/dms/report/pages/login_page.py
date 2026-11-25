"""Page Object handling Robo2mation login, logout, and user session switching."""
from __future__ import annotations

from contextlib import nullcontext

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class LoginError(RuntimeError):
    """Raised when signing in to Robo2mation fails."""


class LoginPage(BasePage):
    """Encapsulates authentication actions using Selenium Page Object Model."""

    USERNAME_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Username')]")
    PASSWORD_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Password')]")
    MESSAGE_SELECTORS = (
        ".toast, .alert, .swal2-popup, [role='alert'], .snackbar, "
        ".Toastify__toast, .ant-message, .growl-animated, [data-notify]"
    )
    LOGOUT_ROUTE = "/login/logout/"

    def __init__(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        base_url: str,
        reporter=None,
    ):
        super().__init__(driver, wait)
        self.base_url = (base_url or "").rstrip("/")
        self.reporter = reporter

    def _step(self, title: str):
        if self.reporter and self.reporter.test_uuid:
            return self.reporter.step(title)
        return nullcontext()

    def is_login_page_displayed(self, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.USERNAME_INPUT)
            )
            return True
        except TimeoutException:
            return False

    def clear_session(self) -> None:
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script(
                "window.localStorage.clear(); window.sessionStorage.clear();"
            )
        except Exception:
            pass

    def get_popup_message(self) -> str:
        messages = [
            el.text.strip()
            for el in self.visible_elements(By.CSS_SELECTOR, self.MESSAGE_SELECTORS)
            if el.text.strip()
        ]
        return " | ".join(messages)

    def login_as(self, username: str, password: str) -> None:
        if not self.base_url:
            raise LoginError("BASE_URL is not configured in .env.")

        with self._step(f"Sign in as user '{username}'"):
            self.driver.get(self.base_url)
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

            user_field = self.wait.until(
                EC.visibility_of_element_located(self.USERNAME_INPUT)
            )
            user_field.clear()
            user_field.send_keys(username)

            pass_field = self.driver.find_element(*self.PASSWORD_INPUT)
            pass_field.clear()
            pass_field.send_keys(password, Keys.ENTER)

            try:
                self.wait.until(EC.invisibility_of_element_located(self.USERNAME_INPUT))
            except TimeoutException as exc:
                popup = self.get_popup_message() or "no error banner shown"
                raise LoginError(
                    f"Login as '{username}' failed. Check dms/.env. Page message: {popup}"
                ) from exc

    def logout(self) -> None:
        with self._step("Log out of current session"):
            self.driver.get(f"{self.base_url}{self.LOGOUT_ROUTE}")
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

    def switch_user(self, username: str, password: str) -> None:
        with self._step(f"Switch session to user '{username}'"):
            self.logout()
            self.login_as(username, password)
