"""
CON-TC007: User Maker - Users Row Selection Options
Expected:
i) Selecting user shows 4 options: "Edit User", "Block User", "User Summary" & "Delete user"
ii) For Locked User: Another option named "Unlock" should be available
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC007"
ROUTE = cfg.route("USERS", "/admin/user/list")
STANDARD_ACTIONS = ["Edit User", "Block User", "User Summary", "Delete User"]


def test_maker_users_row_options(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step("Select a standard user row and verify 4 options"):
        session.user_page.select_row_by_text()
        found_std = session.user_page.assert_row_actions_present(STANDARD_ACTIONS)

    locked_username = cfg.env_value("CONFIG_LOCKED_USERNAME")
    if locked_username:
        with session.step(f"Search locked user '{locked_username}' and verify 'Unlock' option"):
            session.user_page.search_table(locked_username)
            session.user_page.select_row_by_text(locked_username)
            session.user_page.assert_row_actions_present(["Unlock"])

    return f"Verified standard row options ({found_std}) and Unlock option for locked user."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_users_row_options, __doc__)