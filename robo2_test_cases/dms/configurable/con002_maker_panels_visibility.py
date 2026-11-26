"""
CON-TC002: User Maker - Users & User Approval Requests Panels Visibility
1. Login as User with "User Maker" Permission
Expected: Should see both "Users" (approved list) & "User Approval Requests" (approved, pending & rejected) panels
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC002"
ROUTE = cfg.route("USERS", "/admin/user/list")


def test_maker_panels_visibility(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step("Verify both Users and User Approval Requests panels are visible"):
        session.user_page.assert_panels_visible()
        users_header = session.user_page.assert_page_header_contains("Users")
        user_rows = len(session.user_page.assert_table_has_rows("Users"))

    with session.step("Open User Approval Requests panel and verify table loads"):
        session.user_page.open_approval_requests_panel()
        approval_header = session.user_page.assert_page_header_contains("User Approval Requests")
        if "/admin/user/list" in session.driver.current_url.casefold():
            raise AssertionError(
                f"Expected navigation away from /admin/user/list, but URL remained {session.driver.current_url}."
            )
        approval_rows = len(session.user_page.assert_table_has_rows("User Approval Requests"))

    return (
        f"User Maker verified both panels: '{users_header}' (rows={user_rows}) "
        f"and '{approval_header}' (rows={approval_rows})."
    )


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_panels_visibility, __doc__)