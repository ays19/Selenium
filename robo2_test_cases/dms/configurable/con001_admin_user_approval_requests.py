"""
CON-TC001: Admin - Users / User Approval Request
1. Login as User with "Admin" role
2. Go to /admin/user/role_list (and Users / User Approval Requests)
Expected:
i) Should see "Users" & "User Approval Requests" list
ii) Should be able to send User Approval Requests & approve/reject creation/update requests
iii) Search, sort & download should work accordingly
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC001"
ROUTE = cfg.route("ROLE_LIST", "/admin/user/role_list")


def test_admin_user_approval_requests(session: c.ConfigurableSession) -> str:
    session.login_as_role("admin")
    session.open_route(ROUTE)
    with session.step("Verify Users & User Approval Requests panels are visible"):
        session.user_page.assert_panels_visible()

    session.open_route(cfg.route("USERS", "/admin/user/list"))
    with session.step("Verify Search, Sort, and Download on Users list"):
        session.user_page.search_table("admin")
        sorted_col = session.user_page.sort_first_sortable_column()
        session.user_page.download_export("Copy", cfg.download_dir())

    return f"Admin verified Users & Approval panels, search, sort ('{sorted_col}'), and export."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_admin_user_approval_requests, __doc__)