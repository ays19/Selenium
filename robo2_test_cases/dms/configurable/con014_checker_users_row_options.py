"""
CON-TC014: User Checker - Users Row Selection Options
Expected:
i) By selecting user 2 options should be available for all users: "Block User", "User Summary".
ii) For Locked User: Another option named "Unlock" should be available.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC014"
ROUTE = cfg.route("USERS", "/admin/user/list")
STANDARD_ACTIONS = ["Block User", "User Summary"]


def test_checker_users_row_options(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)
    with session.step("Select a standard user row and verify 2 Checker options"):
        session.user_page.select_row_by_text()
        found_std = session.user_page.assert_row_actions_present(STANDARD_ACTIONS)

    locked_username = cfg.env_value("LOCKED_USERNAME")
    if locked_username:
        with session.step(f"Search locked user '{locked_username}' and verify 'Unlock' option"):
            session.user_page.search_table(locked_username)
            session.user_page.select_row_by_text(locked_username)
            session.user_page.assert_row_actions_present(["Unlock"])

    return f"Checker verified Users row options ({found_std}) and Unlock option for locked user."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_users_row_options, __doc__)