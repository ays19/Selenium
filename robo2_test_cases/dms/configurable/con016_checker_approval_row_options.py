"""
CON-TC016: User Checker - User Approval Requests Row Options & Mandatory Reject Comment
Expected:
i) By selecting user 4 options should be available: "Approve User", "Reject User", "View Changes" & "User Summary".
Notes: While rejecting a user a comment is optional.
"""
import common as c
import configurable_config as cfg

TEST_CASE_ID = "CON-TC016"
ROUTE = cfg.route("APPROVAL", "/admin/user/user-creation-requests/")
EXPECTED_ACTIONS = ["Approve User", "Reject User", "View Changes", "User Summary"]


def test_checker_approval_row_options(session: c.ConfigurableSession) -> str:
    session.login_as_role("user_checker")
    session.open_route(ROUTE)

    with session.step("Select pending request and verify 4 Checker options"):
        session.user_page.select_pending_update_request(session.base_url, ROUTE)
        found = session.user_page.assert_row_actions_present(EXPECTED_ACTIONS)

    with session.step("Verify Reject User action with optional comment"):
        session.user_page.click_row_action("Reject User")
        session.user_page.reject_selected_request("QA reject comment check (CON-TC016)", verify_mandatory=False)

    return f"Checker verified all 4 Approval Request options ({found}) and Reject User action."


if __name__ == "__main__":
    c.run_configurable_test(TEST_CASE_ID, ROUTE, test_checker_approval_row_options, __doc__)