"""
CON-TC008: User Maker - User Approval Requests Sort, Search, Toggle, Filter & Download
Expected: Sort, Search, Toggle, Filter & Download should work properly
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC008"
ROUTE = cfg.route("APPROVAL", "/admin/user/user-creation-requests/")


def test_maker_approval_table_controls(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step("Verify Sort, Search, Column Toggle, Filter Drawer, and Download"):
        sorted_col = session.user_page.sort_first_sortable_column()
        session.user_page.search_table("a")
        session.user_page.test_column_toggle()
        session.user_page.open_filter_drawer()
        session.user_page.download_export("Copy", cfg.download_dir())

    return f"User Approval Requests Sort ('{sorted_col}'), Search, Toggle, Filter & Download verified."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_approval_table_controls, __doc__)