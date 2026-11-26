"""
CON-TC013: User Checker - Users List Sort, Search, Toggle & Download
Expected: Sort, Search, Toggle & Download should work properly.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC013"
ROUTE = cfg.route("USERS", "/admin/user/list")


def test_checker_users_table_controls(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step("Verify Sort, Search, Column Toggle, and Download on Users list"):
        session.user_page.search_table("admin")
        sorted_col = session.user_page.sort_first_sortable_column()
        session.user_page.test_column_toggle()
        session.user_page.download_export("Copy", cfg.download_dir())
        downloaded = session.user_page.download_export("CSV", cfg.download_dir())

    return f"Checker Users table Sort ('{sorted_col}'), Search, Toggle & Download ({downloaded.name if downloaded else 'Copy'}) verified."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_users_table_controls, __doc__)