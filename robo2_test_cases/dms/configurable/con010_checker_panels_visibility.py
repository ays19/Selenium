"""
CON-TC010: User Checker - Users & User Approval Requests Panels Visibility
1. Login as User with "User Checker" Permission
Expected: Should see both "Users" (approved list) & "User Approval Requests" (approved, pending & rejected) panels
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC010"
ROUTE = cfg.route("USERS", "/admin/user/list")


def test_checker_panels_visibility(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step("Verify Users & User Approval Requests panels are visible"):
        session.user_page.assert_panels_visible()
        user_rows = len(session.user_page.visible_rows())

    session.open_route(cfg.route("APPROVAL", "/admin/user/approval-requests/"))
    with session.step("Verify User Approval Requests panel loads"):
        approval_rows = len(session.user_page.visible_rows())

    return f"User Checker verified both panels (Users rows={user_rows}, Approval rows={approval_rows})."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_panels_visibility, __doc__)