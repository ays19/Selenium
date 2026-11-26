"""
CON-TC019: Rejected User Behavior
Expected:
i) System shouldn't allow user to login & should show "Please enter a correct user name and password. Note that both fields may be case-sensitive."
ii) New user request should be sent with that user's username & password
iii) Shouldn't show on "Users" list
"""
import time
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC019"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")
EXPECTED_ERROR = "Please enter a correct user name and password"


def test_rejected_user_behavior(session: c.ConfigurableSession) -> str:
    ts = int(time.time()) % 100000
    rej_user = cfg.env_value("REJECTED_TEST_USERNAME", f"qa_rej_{ts}")
    rej_pass = cfg.env_value("REJECTED_TEST_PASSWORD", "QaTest@1234")
    rej_email = f"{rej_user}@example.com"

    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step(f"Maker creates new user request '{rej_user}'"):
        session.user_page.create_user_request(rej_user, rej_pass, rej_email)

    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step(f"Checker rejects user request '{rej_user}'"):
        session.user_page.search_table(rej_user)
        session.user_page.select_row_by_text(rej_user)
        session.user_page.reject_selected_request("Rejecting for CON-TC019 verification")

    with session.step("Verify rejected user does NOT appear on Users list"):
        session.open_route(cfg.route("USERS", "/admin/user/list"))
        session.user_page.assert_user_presence(rej_user, should_exist=False)

    session.login_page.logout_if_needed(session.base_url)
    with session.step("Verify rejected user cannot login"):
        err = session.login_page.login_expect_error(
            session.base_url, rej_user, rej_pass, EXPECTED_ERROR
        )

    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step(f"Verify Maker can re-submit new user request with same username '{rej_user}'"):
        resubmit_msg = session.user_page.create_user_request(rej_user, rej_pass, rej_email)

    return f"Rejected user '{rej_user}' denied login ('{err[:60]}'), absent from Users list, and re-submitted ('{resubmit_msg}')."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_rejected_user_behavior, __doc__)