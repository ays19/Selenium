"""
CON-TC009: User Maker - User Approval Requests Row Options
Expected: By selecting user 2 options should be available: "Edit User", "User Summary"
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC009"
ROUTE = cfg.route("APPROVAL", "/admin/user/approval-requests/")
EXPECTED_ACTIONS = ["Edit User", "User Summary"]


def test_maker_approval_row_options(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_maker")
    session.open_route(ROUTE)
    with session.step("Select a row in User Approval Requests and verify 2 options"):
        session.user_page.select_row_by_text()
        found = session.user_page.assert_row_actions_present(EXPECTED_ACTIONS)

    return f"User Maker verified Approval Request row options: {found}."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_maker_approval_row_options, __doc__)