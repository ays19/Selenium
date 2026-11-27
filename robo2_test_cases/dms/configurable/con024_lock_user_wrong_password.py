"""
CON-TC024: Lock User
1. Go to login page
2. Try to login with wrong password 5 times
Expected: After 5 failed attempts system should lock that user.
"""
import re
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC024"
ROUTE = "/login/"
LOCKOUT_PATTERN = re.compile(
    r"your account is locked due to unsuccessful login attempts", re.IGNORECASE
)


def test_lock_user_after_five_failed_attempts(session: c.ConfigurableSession) -> str:
    target_username = cfg.env_value("LOCK_TARGET_USERNAME")
    if not target_username:
        raise RuntimeError(
            "Set LOCK_TARGET_USERNAME in dms/configurable/.env.configurable (use a dedicated disposable test account)."
        )

    with session.step(f"Attempt login 5 times with wrong password for '{target_username}'"):
        last_msg = session.login_page.trigger_lockout(
            session.base_url, target_username, attempts=5
        )

    with session.step("Verify account is locked after 5 failed attempts"):
        if not LOCKOUT_PATTERN.search(last_msg):
            # Some builds display the lock message on the attempt immediately following the 5th failure
            last_msg = session.login_page.login_expect_error(
                session.base_url,
                target_username,
                "WrongPass!699",
                "Your account is locked due to unsuccessful login attempts",
            )

    return f"User '{target_username}' locked after 5 failed attempts. Message: '{last_msg[:180]}'."


if __name__ == "__main__":
    c.run_configurable_test(
        TEST_CASE_ID, ROUTE, test_lock_user_after_five_failed_attempts, __doc__
    )