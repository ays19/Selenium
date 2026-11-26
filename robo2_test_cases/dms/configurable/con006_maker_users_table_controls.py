"""
CON-TC006: User Maker - Users List Sort, Search, Toggle & Download
Expected: Sort, Search, Toggle & Download should work properly
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC006"
ROUTE = cfg.route("USERS", "/admin/user/list")


def test_maker_users_table_controls(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step("Verify Sort, Search, Column Toggle, and Download"):
        session.user_page.search_table("admin")
        sorted_col = session.user_page.sort_first_sortable_column()
        session.user_page.test_column_toggle()
        session.user_page.download_export("Copy", cfg.download_dir())
        downloaded = session.user_page.download_export("CSV", cfg.download_dir())

    return f"Users table Sort ('{sorted_col}'), Search, Toggle, and Download ({downloaded.name if downloaded else 'Copy'}) verified."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_users_table_controls, __doc__)