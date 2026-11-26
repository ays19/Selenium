"""
CON-TC018: Approve User (Blocked Status)
Expected:
i) System shouldn't allow user to login & should show "This account is blocked. Please contact with administrator."
ii) System should show the user in all places (Groups, Departments, Branches, Workflow Task, Share Documents, ...)
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC018"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")
EXPECTED_ERROR = "This account is blocked. Please contact with administrator."


def test_approve_blocked_user(session: c.ConfigurableSession) -> str:
    profile = cfg.get_profile("blocked_user")

    if cfg.env_value("APPROVE_PENDING_BLOCKED", "false").lower() == "true":
        session.login_as_role("user_checker")
        session.open_route(ROUTE)
        with session.step(f"Approve pending blocked user '{profile.username}'"):
            session.user_page.search_table(profile.username)
            session.user_page.select_row_by_text(profile.username)
            session.user_page.approve_selected_request()
        session.login_page.logout_if_needed(session.base_url)

    with session.step(f"Verify blocked user '{profile.username}' is restricted from login"):
        err = session.login_page.login_expect_error(
            session.base_url, profile.username, profile.password, EXPECTED_ERROR
        )

    session.login_as_role("admin")
    with session.step("Verify blocked user appears in Users list"):
        session.open_route(cfg.route("USERS", "/admin/user/list"))
        session.user_page.assert_user_presence(profile.username, should_exist=True)

    return f"Blocked user login restricted ('{err[:100]}') and verified visible in system lists."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_approve_blocked_user, __doc__)