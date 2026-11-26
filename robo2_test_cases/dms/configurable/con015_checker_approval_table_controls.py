"""
CON-TC015: User Checker - User Approval Requests Sort, Search, Toggle, Filter & Download
Expected: Sort, Search, Toggle, Filter & Download should work properly.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC015"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")


def test_checker_approval_table_controls(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step("Verify Sort, Search, Toggle, Filter, and Download"):
        sorted_col = session.user_page.sort_first_sortable_column()
        session.user_page.search_table("a")
        session.user_page.test_column_toggle()
        session.user_page.open_filter_drawer()
        session.user_page.download_export("Copy", cfg.download_dir())

    return f"Checker Approval Requests Sort ('{sorted_col}'), Search, Toggle, Filter & Download verified."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_approval_table_controls, __doc__)