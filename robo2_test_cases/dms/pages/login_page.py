"""Page Object handling Robo2mation authentication and user session switching."""
from __future__ import annotations

from contextlib import nullcontext

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import dms_config as cfg

from .base_page import BasePage, SetupError


class LoginError(SetupError):
    """Raised when signing in to Robo2mation fails."""


class LoginPage(BasePage):
    """Encapsulates login, logout, and second-user session switching."""

    USERNAME_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Username')]")
    PASSWORD_INPUT = (By.XPATH, "//input[contains(@placeholder, 'Password')]")
    LOGOUT_ROUTE = "/login/logout/"

    def __init__(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        base_url: str = cfg.BASE_URL,
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
        except Exception:
            pass
        try:
            self.driver.execute_script(
                "window.localStorage.clear(); window.sessionStorage.clear();"
            )
        except Exception:
            pass

    def login(self, username: str = cfg.USERNAME, password: str = cfg.PASSWORD) -> None:
        """Initial sign-in using primary credentials from .env."""
        if not self.base_url:
            raise LoginError("BASE_URL is not configured in .env.")
        if not username or not password:
            raise LoginError("DMS_USERNAME and DMS_PASSWORD must be configured in .env.")
        self.login_as(username, password)

    def login_as(self, username: str, password: str) -> None:
        with self._step(f"Sign in as user '{username}'"):
            self.driver.get(self.base_url)
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

            user_field = self.wait.until(EC.visibility_of_element_located(self.USERNAME_INPUT))
            user_field.clear()
            user_field.send_keys(username)

            pass_field = self.driver.find_element(*self.PASSWORD_INPUT)
            pass_field.clear()
            pass_field.send_keys(password, Keys.ENTER)

            try:
                self.wait.until(EC.invisibility_of_element_located(self.USERNAME_INPUT))
            except TimeoutException as exc:
                popup = self.popup_text() or "nothing"
                raise LoginError(
                    f"Login as '{username}' failed (still on login page). Check .env. Page said: {popup}"
                ) from exc

    def logout(self) -> None:
        with self._step("Log out of current session"):
            self.driver.get(f"{self.base_url}{self.LOGOUT_ROUTE}")
            if not self.is_login_page_displayed(timeout=5):
                self.clear_session()
                self.driver.get(self.base_url)

    def as_other_user(
        self,
        function,
        other_user: str | None = None,
        other_pass: str | None = None,
        primary_user: str = cfg.USERNAME,
        primary_pass: str = cfg.PASSWORD,
    ):
        """Log in as the second user, run function(), and restore the primary user session."""
        u2 = other_user or cfg.OTHER_USERNAME
        p2 = other_pass or cfg.OTHER_PASSWORD
        if not (u2 and p2):
            raise LoginError("OTHER_USERNAME and OTHER_PASSWORD must be set in .env.")

        self.logout()
        try:
            self.login_as(u2, p2)
        except LoginError as exc:
            raise LoginError(f"SECOND user (OTHER_USERNAME / OTHER_PASSWORD in .env): {exc}") from exc

        try:
            return function()
        finally:
            self.logout()
            try:
                self.login_as(primary_user, primary_pass)
            except LoginError as exc:
                raise LoginError(
                    f"MAIN user could not log back in after the second-user step: {exc}"
                ) from exc
